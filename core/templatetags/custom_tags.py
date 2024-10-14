from django import template

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