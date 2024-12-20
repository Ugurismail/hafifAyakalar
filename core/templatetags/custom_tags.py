import re
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from core.models import Question


register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Sözlükten (dictionary) verilen anahtara (key) göre bir öğeyi alır.
    """
    return dictionary.get(key, 0)  # Varsayılan değer olarak 0 döndürüyoruz

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
        # Generate HTML link
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
            # Soru yoksa yeni başlık oluşturma linki verelim
            create_url = reverse('add_question_from_search') + f'?q={ref_text}'
            return f'<a href="{create_url}" style="color: #0d6efd; text-decoration: none;">{ref_text}</a>'

    return re.sub(pattern, replace_ref, text)