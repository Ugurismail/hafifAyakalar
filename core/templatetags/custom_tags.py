import re
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from core.models import Question, PollVote, Definition

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
