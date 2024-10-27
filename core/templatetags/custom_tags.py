import re
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

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
        # Markdown link formatını kullanıyoruz
        return f'(bkz: [{query}]({url}))'
    return re.sub(pattern, replace, text)
