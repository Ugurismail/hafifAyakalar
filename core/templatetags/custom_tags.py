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
        return f'(bkz: <a href="{url}" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">{query}</a>)'

    return mark_safe(re.sub(pattern, replace, text))


@register.filter
def ref_link(text):
    pattern = r'\(ref:([^\)]+)\)'
    def replace_ref(match):
        ref_text = match.group(1).strip()
        try:
            q = Question.objects.get(question_text__iexact=ref_text)
            url = reverse('question_detail', args=[q.id])
            return f'<a href="{url}" target="_blank" style="text-decoration: none;">{ref_text}</a>'
        except Question.DoesNotExist:
            create_url = reverse('add_question_from_search') + f'?q={ref_text}'
            return f'<a href="{create_url}" target="_blank" style="text-decoration: none;">{ref_text}</a>'

    # Sonucu mark_safe() ile işaretleyerek HTML'nin render edilmesini sağlıyoruz.
    return mark_safe(re.sub(pattern, replace_ref, text))

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
    Metin içerisinde (tanim:Özgürlük:42) kalıplarını yakalayıp, popover oluşturur.
    """
    if not text:
        return ""

    # Yeni pattern: (tanim:kelime:ID)
    #  Grup 1 => kelime
    #  Grup 2 => id
    pattern = re.compile(r'\(tanim:([^:]+):(\d+)\)')

    def replacer(match):
        question_word = match.group(1).strip()  # "Özgürlük"
        def_id_str    = match.group(2).strip()  # "42"
       

        try:
            definition = Definition.objects.get(id=def_id_str)
            # Tanım metni
            def_text   = definition.definition_text
            # (İstersen "definition.user.username" vs. de popover’a ekleyebilirsin.)
            user_name = definition.user.username


            # HTML popover
            # Bootstrap 5: data-bs-toggle="popover" data-bs-content="..."
            # Hover/focus ile açtırmak için -> data-bs-trigger="hover focus"
            return f'''<span class="tanim-popover" 
                          style="text-decoration:underline; cursor:pointer;"
                          data-bs-toggle="popover" 
                          data-bs-placement="top" 
                          data-bs-trigger="hover focus"
                          data-bs-title="{user_name}"
                          data-bs-content="{def_text}">
                          {question_word}
                       </span>'''
        except Definition.DoesNotExist:
            # ID bulunamadıysa => orijinal metni döndürmek yerine 
            # plain text olarak "kelime" döndürebiliriz veya "Tanım yok" diyen bir span.
            return question_word

    # text içinde tüm (tanim:word:id) kalıplarını replacer ile değiştir.
    new_text = pattern.sub(replacer, text)

    return mark_safe(new_text)

@register.filter
def reference_link(text):
    """
    Metin içinde (kaynak:ID[, sayfa:NUM]) kalıplarını yakalar.
    Her unique ID için sırayla [1], [2], [3] vs. gösterir.
    Hover (veya tooltip) ile tam künyeyi gösterir.
    """
    if not text:
        return ""

    reference_map = {}
    current_index = 1

    pattern = r'\(kaynak:(\d+)(?:,\s*sayfa:(\d+))?\)'

    def replace_reference(match):
        nonlocal current_index
        ref_id_str = match.group(1)
        sayfa = match.group(2)  # Opsiyonel: None veya sayfa numarası
        ref_id = int(ref_id_str)

        if ref_id not in reference_map:
            reference_map[ref_id] = current_index
            current_index += 1

        ref_num = reference_map[ref_id]

        try:
            ref_obj = Reference.objects.get(id=ref_id)
            full_citation = f"{ref_obj.author_surname}, {ref_obj.author_name} ({ref_obj.year}). {ref_obj.rest}"
            if ref_obj.abbreviation:
                full_citation += f" [{ref_obj.abbreviation}]"
            if sayfa:
                full_citation += f", s. {sayfa}"
        except Reference.DoesNotExist:
            full_citation = f"Kaynak bulunamadı (ID: {ref_id})"

        html = f'<sup class="reference-tooltip" data-bs-toggle="tooltip" title="{full_citation}">[{ref_num}]</sup>'
        return html

    new_text = re.sub(pattern, replace_reference, text)
    return mark_safe(new_text)

@register.filter
def highlight(text, keyword):
    """
    'text' içinde 'keyword' kelimesi geçiyorsa, 
    <mark>...</mark> ile vurgulansın (case-insensitive).
    """
    if not keyword:
        return text  # aranan kelime boşsa, değiştirmeden dön

    # Tüm 'keyword' geçen yerleri bul, <mark> ekle
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<mark>{m.group(0)}</mark>',
        text
    )
    return mark_safe(highlighted)

@register.filter
def mention_link(text):
    import re
    from django.contrib.auth.models import User  # Kullanıcı modelini içe aktarıyoruz
    pattern = r'@(\w+)'  # @ işaretinden sonra gelen harf/ sayı/alt çizgi kombinasyonunu yakalar

    def replace(match):
        username = match.group(1)
        try:
            user = User.objects.get(username__iexact=username)
            url = reverse('user_profile', args=[user.username])
            # İsteğe bağlı: "mention" adında bir CSS sınıfı ekleyebilirsiniz
            return f'<a href="{url}" class="mention">@{username}</a>'
        except User.DoesNotExist:
            # Böyle bir kullanıcı yoksa orijinal metni bırakıyoruz
            return f'@{username}'

    new_text = re.sub(pattern, replace, text)
    return mark_safe(new_text)