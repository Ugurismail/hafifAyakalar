from django.contrib import admin
from .models import (Invitation, UserProfile, Question, Answer, 
                     Poll, PollOption, PollVote, SavedItem, Vote, PinnedEntry, Entry, RandomSentence)

admin.site.register(Invitation)
admin.site.register(UserProfile)
admin.site.register(SavedItem)
admin.site.register(Vote)
admin.site.register(PinnedEntry)
admin.site.register(Entry)
admin.site.register(RandomSentence)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['question_text']
    list_display = ['question_text', 'user', 'created_at']
    list_filter = ['created_at', 'user']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    search_fields = ['answer_text', 'question__question_text']
    list_display = ['short_answer', 'question', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    def short_answer(self, obj):
        return obj.answer_text[:50]
    short_answer.short_description = 'Yanıt Metni'

    def question_text(self, obj):
        return obj.question.question_text
    question_text.short_description = 'Soru Metni'

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'created_by', 'created_at', 'end_date', 'is_anonymous']
    search_fields = ['question_text', 'created_by__username']
    list_filter = ['created_at', 'is_anonymous']

@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ['poll', 'option_text']
    search_fields = ['poll__question_text', 'option_text']

@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'option', 'voted_at']
    search_fields = ['user__username', 'option__option_text']
    list_filter = ['voted_at']
