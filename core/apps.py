# core/apps.py
from django.apps import AppConfig
from django.core.validators import RegexValidator

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.contrib.auth.models import User
        # Yeni doğrulayıcı: harf, rakam, alt çizgi, nokta, @, +, -, ve boşluk
        custom_validator = RegexValidator(
            regex=r'^[\w\s.@+-]+$',
            message="Bu değer sadece harfleri, rakamları, boşluk ve @/./+/-/_ karakterlerini içerebilir.",
            code='invalid_username'
        )
        # Varsayılan username alanındaki tüm doğrulayıcıları bu doğrulayıcı ile değiştiriyoruz.
        User._meta.get_field('username').validators = [custom_validator]
        import core.signals
