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
    subquestions = models.ManyToManyField('self', symmetrical=False, related_name='parent_questions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # parent_questions alanını kaldırdık
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    users = models.ManyToManyField(
        User, related_name='associated_questions', blank=True
    )
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    def __str__(self):
        return self.question_text

    def has_subquestions(self):
        return self.subquestions.exists()

    def get_subquestions(self):
        return self.subquestions.all()

    def get_total_subquestions_count(self, visited=None):
        if visited is None:
            visited = set()
        if self.id in visited:
            return 0
        visited.add(self.id)
        count = 0
        for subquestion in self.subquestions.all():
            count += 1  # Doğrudan alt soruyu say
            count += subquestion.get_total_subquestions_count(visited)  # Alt soruların alt sorularını say
        return count

    class Meta:
        ordering = ['created_at']


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

class StartingQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starting_questions')
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='starter_users'
    )

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text}"

class SavedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, null=True, blank=True
    )
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, null=True, blank=True
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question', 'answer')


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, null=True, blank=True
    )
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, null=True, blank=True
    )
    value = models.IntegerField()  # +1 veya -1

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'], name='unique_user_question_vote'
            ),
            models.UniqueConstraint(
                fields=['user', 'answer'], name='unique_user_answer_vote'
            ),
        ]
