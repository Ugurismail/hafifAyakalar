from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            invitation_quota = 999999999
        else:
            invitation_quota = 0
        UserProfile.objects.create(user=instance, invitation_quota=invitation_quota)
