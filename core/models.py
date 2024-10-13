from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone



class Invitation(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_invitations', null=True, blank=True
    )
    quota_granted = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    used_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='used_invitations', null=True, blank=True
    )

    def __str__(self):
        return f"Invitation from {self.sender.username if self.sender else 'System'}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    invitation_quota = models.PositiveIntegerField(default=0)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

# Kullanıcı oluşturulduğunda otomatik olarak profil oluşturma
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Süper kullanıcıya başlangıç davet hakkı veriyoruz
        if instance.is_superuser:
            invitation_quota = 999999999
        else:
            invitation_quota = 0
        UserProfile.objects.create(user=instance, invitation_quota=invitation_quota)


class Question(models.Model):
    question_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return self.question_text
    
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')

    def __str__(self):
        return f"Answer to {self.question.question_text} by {self.user.username}"


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages'
    )
    body = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.body[:20]}"

