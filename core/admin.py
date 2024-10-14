from django.contrib import admin
from .models import Invitation, UserProfile
from .models import Question, Answer

admin.site.register(Invitation)
admin.site.register(UserProfile)

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