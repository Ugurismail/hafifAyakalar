import re
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from core.models import Question, PollVote, Definition,Reference



register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

@register.filter
def dict_get(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def bkz_link(text):
    pattern = r'\(bkz:\s*(.*?)\)'
    def replace(match):
        query = match.group(1).strip()
        url = reverse('bkz', args=[query])
        return f'(bkz: <a href="{url}">{query}</a>)'
    return mark_safe(re.sub(pattern, replace, text))

@register.filter
def ref_link(text):
    pattern = r'\(ref:([^\)]+)\)'
    def replace_ref(match):
        ref_text = match.group(1).strip()
        try:
            q = Question.objects.get(question_text__iexact=ref_text)
            url = reverse('question_detail', args=[q.id])
            return f'<a href="{url}" style="color: #0d6efd; text-decoration: none;">{ref_text}</a>'
        except Question.DoesNotExist:
            create_url = reverse('add_question_from_search') + f'?q={ref_text}'
            return f'<a href="{create_url}" style="color: #0d6efd; text-decoration: none;">{ref_text}</a>'

    return re.sub(pattern, replace_ref, text)

@register.filter
def user_has_voted(options, user):
    return PollVote.objects.filter(option__in=options, user=user).exists()

@register.filter
def field_by_name(form, name):
    return form[name]

@register.filter
def split(value, separator=' '):
    return value.split(separator)

@register.filter
def tanim_link(text):
    """
    Metin içerisinde (tanim:Özgürlük) gibi kalıpları bulup, popover linkine dönüştürür.
    """
    pattern = r'\(tanim:([^)]+)\)'  # (tanim:kelime)
    def replace_tanim(match):
        word = match.group(1).strip()
        # word’e karşılık veritabanında bir Definition var mı? 
        # NOT: user’a göre, ya da en güncel tanımı alabilirsin. 
        # Kolay olması açısından: 
        definition = Definition.objects.filter(question__question_text__iexact=word).order_by('-created_at').first()
        if definition:
            # HTML popover oluştur
            # Bootstrap popover kullanacaksan -> data-bs-toggle="popover" data-bs-content="..."
            # Renk için style ekleyebilirsin
            return f'<span class="tanim-popover" ' \
                   f'style="color: green; text-decoration: underline; cursor: pointer;" ' \
                   f'data-bs-toggle="popover" data-bs-placement="top" data-bs-trigger="hover focus" ' \
                   f'data-bs-content="{definition.definition_text}">{word}</span>'
        else:
            # Tanım yoksa, normal göster
            return word

    return mark_safe(re.sub(pattern, replace_tanim, text))



@register.filter
def reference_link(text):
    """
    Metin içinde (kaynak:ID) kalıplarını yakalar.
    Her unique ID için sırayla [1], [2], [3] vs. gösterir.
    Hover (veya tooltip) ile tam künyeyi gösterir.
    """
    if not text:
        return ""

    # Bu sözlük "reference_id -> kaçıncı kaynak" eşleşmesini tutacak
    reference_map = {}
    current_index = 1

    # Regex: (kaynak:XX) => grup1: '(kaynak:XX)', grup2: 'XX'
    pattern = r'\(kaynak:(\d+)\)'

    def replace_reference(match):
        nonlocal current_index
        ref_id_str = match.group(1)  # '12'
        ref_id = int(ref_id_str)

        # Daha önce bu ref_id gördüysek aynı numarayı kullan
        if ref_id not in reference_map:
            reference_map[ref_id] = current_index
            current_index += 1

        ref_num = reference_map[ref_id]

        # Veritabanından kaynağı çek
        try:
            ref_obj = Reference.objects.get(id=ref_id)
            # Örnek künye: "Bellah, R. (2017). İnsan Evriminde Din..."
            # Kendi formatınızı oluşturabilirsiniz
            full_citation = f"{ref_obj.author_surname}, {ref_obj.author_name} ({ref_obj.year}). {ref_obj.rest}"
            if ref_obj.abbreviation:
                full_citation += f" [{ref_obj.abbreviation}]"
        except Reference.DoesNotExist:
            # Kaynak yoksa mecburen "?" veya benzeri bir gösterim
            full_citation = f"Kaynak bulunamadı (ID: {ref_id})"

        # HTML çıktı
        # Örneğin <sup> etiketinde tooltip/popover. 
        # Bootstrap 5 tooltip => data-bs-toggle="tooltip" title="..."
        # Popover kullanacaksan data-bs-toggle="popover" data-bs-content="..."
        # Burada tooltip örneği verelim:
        html = f'<sup class="reference-tooltip" data-bs-toggle="tooltip" title="{full_citation}">[{ref_num}]</sup>'
        return html

    # re.sub ile text içindeki tüm (kaynak:XX) kalıplarını replace_reference fonksiyonuyla değiştir
    new_text = re.sub(pattern, replace_reference, text)
    return mark_safe(new_text)  # HTML etiketlerini güvenli işaretle
