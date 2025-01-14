import re
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.models import Question, PollVote, Definition, Reference

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """dictionary[key] veya 0 döndürür."""
    return dictionary.get(key, 0)


@register.filter
def dict_get(dictionary, key):
    """dictionary[key] veya None döndürür."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def bkz_link(text):
    """
    Metindeki (bkz: kelime) kalıplarını linke dönüştürür.
    Örn. (bkz: Python) -> (bkz: <a href="/bkz/Python">Python</a>)
    """
    pattern = r'\(bkz:\s*(.*?)\)'

    def replace(match):
        query = match.group(1).strip()
        url = reverse('bkz', args=[query])
        return f'(bkz: <a href="{url}">{query}</a>)'

    return mark_safe(re.sub(pattern, replace, text))


@register.filter
def ref_link(text):
    """
    Metindeki (ref:kelime) kalıplarını soru linkine (veya 'add question' linkine) dönüştürür.
    Örn. (ref:Python) => /question_detail/pk ...
    """
    pattern = r'\(ref:([^\)]+)\)'

    def replace_ref(match):
        ref_text = match.group(1).strip()
        try:
            q = Question.objects.get(question_text__iexact=ref_text)
            url = reverse('question_detail', args=[q.id])
            return f'<a href="{url}" style="text-decoration: none;">{ref_text}</a>'
        except Question.DoesNotExist:
            # Soru yoksa, 'add_question_from_search' yoluna yönlendir
            create_url = reverse('add_question_from_search') + f'?q={ref_text}'
            return f'<a href="{create_url}" style="text-decoration: none;">{ref_text}</a>'

    return mark_safe(re.sub(pattern, replace_ref, text))


@register.filter
def user_has_voted(options, user):
    """Bir anket seçeneğine oy verip vermediğini kontrol."""
    return PollVote.objects.filter(option__in=options, user=user).exists()


@register.filter
def field_by_name(form, name):
    """Form alanına ismen erişmek için."""
    return form[name]


@register.filter
def split(value, separator=' '):
    """Bir string'i verilen ayraca göre listeye böler."""
    return value.split(separator)


@register.filter(name='tanim_link')
def tanim_link(text, answer_user):
    """
    Metindeki (tanim:Kelime) kalıplarını,
    -> Cevabın sahibi 'answer_user' hangi question_text = Kelime için tanım yapmışsa,
       onun tanımını tooltip/popover şeklinde gösteren bir HTML <span> oluşturur.
    Örneğin (tanim:X) => "X" yazacak, hover'da user'ın X tanımı görünecek.

    Template kullanımı:
        {{ answer.answer_text|linebreaksbr|tanim_link:answer.user|safe }}

    Not: "linebreaksbr" vb. filtreyi senin ihtiyacına göre ekleyebilirsin.
    """

    if not text:
        return ""

    pattern = r'\(tanim:([^)]+)\)'  # mesela (tanim:Özgürlük)

    def replace_tanim(match):
        word = match.group(1).strip()  # "Özgürlük"
        # "word" adlı question_text'i bulmaya çalış
        # NOT: Her kullanıcı, question_text'i "X" olan bir Definition girmiş olabilir.
        # Biz 'answer_user' bazlı alıyoruz (bu cevabı kim yazmışsa, onun tanımını).
        definition_qs = Definition.objects.filter(
            question__question_text__iexact=word,
            user=answer_user
        ).order_by('-created_at')

        if definition_qs.exists():
            definition = definition_qs.first()  # en son girilen tanım
            definition_text = definition.definition_text
            # HTML popover (BS5) veya tooltip yapabilirsin.
            # Aşağıdaki örnek popover:
            return (
                f'<span class="tanim-popover" '
                f'style="text-decoration: underline; cursor: pointer;" '
                f'data-bs-toggle="popover" data-bs-placement="top" data-bs-trigger="hover focus" '
                f'data-bs-content="{definition_text}">{word}</span>'
            )
        else:
            # Kullanıcının o question_text için tanımı yoksa, normal kelimeyi göstermek.
            return word

    new_text = re.sub(pattern, replace_tanim, text)
    return mark_safe(new_text)


@register.filter
def reference_link(text):
    """
    Metin içindeki (kaynak:ID) kalıplarını bulur, her ID için [1], [2], [3] gibi
    numaralandırma yapar. Hover'da tam künye gösterir (tooltip).
    Örneğin:
       "... (kaynak:12) ..." -> ".... <sup title='Bellah, R. (2017)...'>[1]</sup> ..."
    """

    if not text:
        return ""

    reference_map = {}
    current_index = 1
    pattern = r'\(kaynak:(\d+)\)'

    def replace_reference(match):
        nonlocal current_index
        ref_id_str = match.group(1)  # "12"
        ref_id = int(ref_id_str)

        # Aynı ID'ye tekrar rastlarsak aynı numarayı kullanalım
        if ref_id not in reference_map:
            reference_map[ref_id] = current_index
            current_index += 1

        ref_num = reference_map[ref_id]

        try:
            ref_obj = Reference.objects.get(id=ref_id)
            # Örnek künye: "Bellah, R. (2017). rest..."
            full_citation = f"{ref_obj.author_surname}, {ref_obj.author_name} ({ref_obj.year}). {ref_obj.rest}"
            if ref_obj.abbreviation:
                full_citation += f" [{ref_obj.abbreviation}]"
        except Reference.DoesNotExist:
            full_citation = f"Kaynak bulunamadı (ID: {ref_id})"

        # Bootstrap tooltip kullanıyoruz
        html = (
            f'<sup class="reference-tooltip" '
            f'data-bs-toggle="tooltip" title="{full_citation}">'
            f'[{ref_num}]</sup>'
        )
        return html

    new_text = re.sub(pattern, replace_reference, text)
    return mark_safe(new_text)
