from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
import datetime



class Invitation(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_invitations', null=True, blank=True
    )
    quota_granted = models.PositiveIntegerField(default=0)  # Eklendi
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='used_invitations', null=True, blank=True
    )

    def __str__(self):
        return f"Invitation from {self.sender.username if self.sender else 'System'}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    invitation_quota = models.PositiveIntegerField(default=0) 
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    # Renk ayarları alanları
    background_color = models.CharField(max_length=7, default='#F5F5F5')
    text_color = models.CharField(max_length=7, default='#000000')
    header_background_color = models.CharField(max_length=7, default='#ffffff')
    header_text_color = models.CharField(max_length=7, default='#333333')
    link_color = models.CharField(max_length=7, default='#0d6efd')
    link_hover_color = models.CharField(max_length=7, default='#0056b3')
    button_background_color = models.CharField(max_length=7, default='#007bff')
    button_hover_background_color = models.CharField(max_length=7, default='#0056b3')
    button_text_color = models.CharField(max_length=7, default='#ffffff')
    hover_background_color = models.CharField(max_length=7, default='#f0f0f0')
    icon_color = models.CharField(max_length=7, default='#333333')
    icon_hover_color = models.CharField(max_length=7, default='#007bff')
    answer_background_color = models.CharField(max_length=7, default='#F5F5F5')
    content_background_color = models.CharField(max_length=7, default='#ffffff')
    tab_background_color = models.CharField(max_length=7, default='#f8f9fa')
    tab_text_color = models.CharField(max_length=7, default='#000000')
    tab_active_background_color = models.CharField(max_length=7, default='#ffffff')
    tab_active_text_color = models.CharField(max_length=7, default='#000000')
    dropdown_text_color = models.CharField(max_length=7, default='#333333')
    dropdown_hover_background_color = models.CharField(max_length=7, default='#f2f2f2')
    dropdown_hover_text_color = models.CharField(max_length=7, default='#0056b3')
    nav_link_hover_color = models.CharField(max_length=7, default='#007bff')
    nav_link_hover_bg = models.CharField(max_length=7, default='rgba(0, 0, 0, 0.05)')
    pagination_background_color = models.CharField(max_length=7, default='#ffffff')
    pagination_text_color = models.CharField(max_length=7, default='#000000')
    pagination_active_background_color = models.CharField(max_length=7, default='#007bff')
    pagination_active_text_color = models.CharField(max_length=7, default='#ffffff')

    # Diğer renk alanlarını da ekleyin

    def __str__(self):
        return f"{self.user.username}'s profile"


class Question(models.Model):
    question_text = models.CharField(max_length=255)
    subquestions = models.ManyToManyField('self', symmetrical=False, related_name='parent_questions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    from_search = models.BooleanField(default=False) 
    saveditem = GenericRelation('SavedItem')
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
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    saveditem = GenericRelation('SavedItem')

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
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def save(self, *args, **kwargs):
        if not self.content_type and not self.object_id:
            if hasattr(self, 'question'):
                self.content_type = ContentType.objects.get_for_model(Question)
                self.object_id = self.question.id
            elif hasattr(self, 'answer'):
                self.content_type = ContentType.objects.get_for_model(Answer)
                self.object_id = self.answer.id
        super(SavedItem, self).save(*args, **kwargs)

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField()  # +1 or -1

    # New fields made non-nullable
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Remove old fields
    # question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, blank=True)
    # answer = models.ForeignKey('Answer', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

class PinnedEntry(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"PinnedEntry of {self.user.username}"

class Entry(models.Model):
    # Soru ve yanıtları temsil eden soyut bir model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

class RandomSentence(models.Model):
    sentence = models.CharField(max_length=280)

    def __str__(self):
        return self.sentence[:50]
    



class Poll(models.Model):
    question_text = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_anonymous = models.BooleanField(default=True)
    # İlgili başlık soru modeliyle ilişki (eğer önceden Question modeli tanımlandıysa)
    related_question = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, blank=True)

    def is_active(self):
        return timezone.now() < self.end_date

    def duration_ok(self):
        # 1 yıldan uzun mu kontrol et
        return self.end_date <= (self.created_at + datetime.timedelta(days=365))

    def __str__(self):
        return self.question_text

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.poll.question_text} - {self.option_text}"

    @property
    def votes_count(self):
        return self.votes.count()

class PollVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'option')

    def __str__(self):
        return f"{self.user.username} -> {self.option.option_text}"