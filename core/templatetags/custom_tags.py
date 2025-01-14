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
    Metinde (bkz: Kelime) kalıplarını linke dönüştürür.
    Örn. (bkz: Python) => (bkz: <a href="/bkz/Python">Python</a>)
    """
    if not text:
        return ""

    pattern = r'\(bkz:\s*(.*?)\)'

    def replace_bkz(match):
        query = match.group(1).strip()
        # /bkz/URL'sine yönlendirmek için
        url = reverse('bkz', args=[query])
        return f'(bkz: <a href="{url}">{query}</a>)'

    new_text = re.sub(pattern, replace_bkz, text)
    return mark_safe(new_text)

@register.filter
def ref_link(text):
    """
    Metinde (ref:Kelime) kalıplarını,
    ilgili Soru sayfasına (question_detail) veya 'add_question_from_search' linkine dönüştürür.

    Örn: (ref:Python) => eğer Python diye bir soru varsa oraya link, yoksa yeni ekleme linki.
    """
    if not text:
        return ""

    pattern = r'\(ref:([^\)]+)\)'

    def replace_ref(match):
        ref_text = match.group(1).strip()
        try:
            q = Question.objects.get(question_text__iexact=ref_text)
            url = reverse('question_detail', args=[q.id])
            return f'<a href="{url}" style="text-decoration: none;">{ref_text}</a>'
        except Question.DoesNotExist:
            create_url = reverse('add_question_from_search') + f'?q={ref_text}'
            return f'<a href="{create_url}" style="text-decoration: none;">{ref_text}</a>'

    new_text = re.sub(pattern, replace_ref, text)
    return mark_safe(new_text)

@register.filter
def user_has_voted(options, user):
    """
    Bir anket seçeneğine (PollOption) oy verip vermediğini kontrol eder.
    """
    return PollVote.objects.filter(option__in=options, user=user).exists()

@register.filter
def field_by_name(form, name):
    """
    Bir Django Form nesnesindeki name alanına erişmek için.
    """
    return form[name]

@register.filter
def split(value, separator=' '):
    """
    Bir string'i belirli bir ayraca göre bölüp liste olarak döndürür.
    """
    return value.split(separator)



@register.filter
def reference_link(text):
    """
    Metindeki (kaynak:ID) kalıplarını [1], [2], [3] gibi sup notlarına dönüştürür.
    Hover'da Reference kaydının tam bilgisini (yazar, yıl, vs.) gösterir.
    """
    if not text:
        return ""

    pattern = r'\(kaynak:(\d+)\)'
    reference_map = {}
    current_index = 1

    def replace_reference(match):
        nonlocal current_index
        ref_id_str = match.group(1)
        ref_id = int(ref_id_str)

        # Aynı ref ID'siyle tekrar karşılaşırsak aynı index numarasını kullanalım
        if ref_id not in reference_map:
            reference_map[ref_id] = current_index
            current_index += 1

        ref_num = reference_map[ref_id]

        # Veritabanından Reference'ı çek
        try:
            ref_obj = Reference.objects.get(id=ref_id)
            full_citation = f"{ref_obj.author_surname}, {ref_obj.author_name} ({ref_obj.year}). {ref_obj.rest}"
            if ref_obj.abbreviation:
                full_citation += f" [{ref_obj.abbreviation}]"
        except Reference.DoesNotExist:
            full_citation = f"Kaynak bulunamadı (ID: {ref_id})"

        # [n] şeklinde tooltip
        html = (
            f'<sup class="reference-tooltip" '
            f'data-bs-toggle="tooltip" title="{full_citation}">'
            f'[{ref_num}]</sup>'
        )
        return html

    new_text = re.sub(pattern, replace_reference, text)
    return mark_safe(new_text)

@register.filter(name='tanim_link')
def tanim_link(text, answer_user=None):
    """
    Metindeki "(tanim:Kelime:UserID)" kalıplarını parse eder.
    Eğer userID belirtilmemişse (yani "(tanim:Kelime)"),
    fallback olarak 'answer_user' (cevabı yazanın) tanımını gösterir.
    """

    if not text:
        return ""

    # 1) (tanim:Kelime:UserID) => pattern_with_user
    pattern_with_user = r'\(tanim:([^:]+):(\d+)\)'

    # 2) (tanim:Kelime) => pattern_no_user (UserID yoksa fallback)
    pattern_no_user   = r'\(tanim:([^)]+)\)'

    def replace_with_user(match):
        question_text = match.group(1).strip()
        user_id_str   = match.group(2).strip()
        user_id       = int(user_id_str)

        return get_tanim_html(question_text, user_id)

    def replace_no_user(match):
        question_text = match.group(1).strip()
        # Bu senaryoda user_id yok, fallback: 'answer_user' varsa onun ID'sini kullan
        if answer_user is not None:
            user_id = answer_user.id
            return get_tanim_html(question_text, user_id)
        else:
            # answer_user da yoksa parse etme
            return f"(tanim:{question_text})"

    def get_tanim_html(q_text, u_id):
        # Soru var mı?
        try:
            q_obj = Question.objects.get(question_text__iexact=q_text)
        except Question.DoesNotExist:
            return f"{q_text} (?)"  # Soru yok

        # Definition var mı?
        def_qs = Definition.objects.filter(question=q_obj, user_id=u_id).order_by('-created_at')
        if def_qs.exists():
            definition_text = def_qs.first().definition_text
            # Tooltip HTML
            html = (f'<span '
                    f'data-bs-toggle="tooltip" '
                    f'data-bs-placement="top" '
                    f'data-bs-custom-class="my-tanim-tooltip" '
                    f'title="{definition_text}" '
                    f'style="text-decoration: underline; cursor: pointer;">'
                    f'{q_text}</span>'
            )
            return html
        else:
            return f"{q_text} (tanım yok)"

    # Önce (tanim:Kelime:UserID) parse
    new_text = re.sub(pattern_with_user, replace_with_user, text)
    # Sonra (tanim:Kelime) parse (fallback => answer_user)
    new_text = re.sub(pattern_no_user, replace_no_user, new_text)

    return mark_safe(new_text)