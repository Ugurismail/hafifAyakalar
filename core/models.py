from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
import datetime
from django.conf import settings
import re




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
    background_color = models.CharField(max_length=7, default='#F5F5F5') #genel arka plan
    text_color = models.CharField(max_length=7, default='#000000')
    message_bubble_color = models.CharField(max_length=7, default='#d1e7ff')
    tbas_color=models.CharField(max_length=7, default='#000000')

    yanit_card = models.CharField(max_length=7, default='#ffffff')
    header_background_color = models.CharField(max_length=7, default='#ffffff')
    header_text_color = models.CharField(max_length=7, default='#333333')
    link_color = models.CharField(max_length=7, default='#6E8CA7')
    link_hover_color = models.CharField(max_length=7, default='#4E647E')

    button_background_color = models.CharField(max_length=7, default='#6E8CA7')
    button_hover_background_color = models.CharField(max_length=7, default='#4E647E')
    button_text_color = models.CharField(max_length=7, default='#ffffff')

    secondary_button_background_color = models.CharField(max_length=7, default='#6c757d')
    secondary_button_hover_background_color = models.CharField(max_length=7, default='#495057')
    secondary_button_text_color = models.CharField(max_length=7, default='#ffffff')

    font_size = models.IntegerField(default='16')

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

    nav_link_hover_bg = models.CharField(max_length=7, default='#f5f5f5')

    pagination_background_color = models.CharField(max_length=7, default='#ffffff')
    pagination_text_color = models.CharField(max_length=7, default='#000000')
    # pagination_active_background_color = models.CharField(max_length=7, default='#007bff')
    # pagination_active_text_color = models.CharField(max_length=7, default='#ffffff')

    font_family = models.CharField(max_length=100, default='EB Garamond')

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
    ignored_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='ignored_random_sentences'
    )

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
    

class Definition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='definitions')
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='definitions')
    definition_text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    answer = models.OneToOneField('Answer', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.question.question_text} / {self.user.username}"
    
class Reference(models.Model):
    author_surname = models.CharField(max_length=100, verbose_name="Yazar Soyadı")
    author_name = models.CharField(max_length=100, verbose_name="Yazar Adı")
    year = models.PositiveIntegerField(verbose_name="Yıl")
    metin_ismi = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Metin İsmi (Opsiyonel)"
    )
    rest = models.TextField(max_length=2000, verbose_name="Künyenin Kalanı")
    abbreviation = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Kısaltma (Opsiyonel)"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='references')

    def __str__(self):
        metin = f", {self.metin_ismi}" if self.metin_ismi else ""
        if self.abbreviation:
            return f"{self.author_surname}, {self.author_name} ({self.year}){metin} - {self.abbreviation}"
        return f"{self.author_surname}, {self.author_name} ({self.year}){metin}"

    def get_usage_count(self):
        """
        Answer modelindeki answer_text alanında, hem (kaynak:REF_ID) 
        hem de (kaynak:REF_ID, sayfa:NUM) şeklinde geçen ifadeleri sayar.
        """
        from .models import Answer  # Lokal import döngüsel importları önlemek için.
        # Regex deseni: 
        # \(kaynak:REF_ID     -> literal olarak "(kaynak:REF_ID"
        # (?:,\s*sayfa:\d+)?   -> opsiyonel olarak ", sayfa:" ile başlayan ve sonrasında bir veya daha fazla rakam
        # \)                   -> kapanış parantezi
        pattern = re.compile(r'\(kaynak:{}(?:,\s*sayfa:\d+)?\)'.format(self.id))
        count = 0
        # İlk filtre, answer_text içerisinde "(kaynak:REF_ID" ifadesi geçiyorsa getiriyor
        answers = Answer.objects.filter(answer_text__icontains=f"(kaynak:{self.id}")
        for answer in answers:
            matches = pattern.findall(answer.answer_text)
            count += len(matches)
        return count
