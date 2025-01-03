from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME


from .models import (
    Invitation, UserProfile, Question, Answer, 
    Poll, PollOption, PollVote, SavedItem, Vote, PinnedEntry, 
    Entry, RandomSentence, Message
)

# -------------------------------------
# 1) Standart Admin Kaydı
# -------------------------------------
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


# -------------------------------------
# 2) Kullanıcıları Seçip Mesaj Gönderme
#    Ara Sayfa Kullanarak
# -------------------------------------

# a) Önce default User kaydını kaldır:
admin.site.unregister(User)


# b) Mesaj Formu: Ara sayfa (intermediate) için basit bir Django Form
from django import forms
from django.contrib import admin

class MassMessageForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.HiddenInput)
    message_body = forms.CharField(
        label="Mesajınız",
        widget=forms.Textarea(attrs={"rows":4, "cols":60}),
        required=True
    )


# c) Yeni Admin Sınıfı
class CustomUserAdmin(UserAdmin):
    actions = ["send_message_to_selected_users"]

    def get_urls(self):
        """
        'Seçili kullanıcılara mesaj gönder' action'ı için
        özel bir ara sayfa URL'si ekliyoruz.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-messages/',
                self.admin_site.admin_view(self.send_messages_intermediate),
                name='send_messages_intermediate',
            )
        ]
        return custom_urls + urls

    def send_message_to_selected_users(self, request, queryset):
        """
        Admin action: seçili kullanıcılara mesaj göndermek için
        bir ara sayfa formuna yönlendireceğiz.
        """
        # Eğer hiç kullanıcı seçilmediyse, doğrudan uyarı verip dönelim
        if not queryset.exists():
            self.message_user(request, "Hiç kullanıcı seçmediniz!", level=messages.WARNING)
            return

        # Seçili kullanıcıların PK'lerini al
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        # Ara sayfa url'sine yönlendiriyoruz (send_messages_intermediate)
        return redirect(
            f"send-messages/?ids={','.join(selected)}"
        )

    send_message_to_selected_users.short_description = "Seçili kullanıcılara mesaj gönder"

    def send_messages_intermediate(self, request):
        """
        Ara sayfa: burada message_body'yi gireceğiz ve
        'apply' dediğimizde asıl mesaj gönderme işlemine geçeceğiz.
        """
        from .models import Message

        # URL'deki param: ?ids=1,2,3
        ids_param = request.GET.get('ids', '')
        if not ids_param:
            self.message_user(request, "Kullanıcı seçilmedi veya geçersiz ID.", level=messages.ERROR)
            return redirect("..")  # Kullanıcı yoksa geri dön

        # Virgülle ayrılmış PK'lerden queryset oluştur
        user_ids = ids_param.split(',')
        selected_users = User.objects.filter(pk__in=user_ids)

        if request.method == 'POST':
            form = MassMessageForm(request.POST)
            if form.is_valid():
                message_body = form.cleaned_data['message_body']
                admin_user = request.user
                count = 0
                for user in selected_users:
                    if user != admin_user:  # Gerekirse
                        Message.objects.create(
                            sender=admin_user,
                            recipient=user,
                            body=message_body
                        )
                        count += 1
                self.message_user(request, f"{count} kullanıcıya mesaj gönderildi.")
                return redirect("/admin/auth/user/")  # Veya user listesinin URL'i

        else:
            # GET isteği => formu göster
            initial_data = {
                '_selected_action': ids_param
            }
            form = MassMessageForm(initial=initial_data)

        return render(request, 'admin/send_message_form.html', {
            'form': form,
            'selected_users': selected_users,
        })


# d) Kayıt: User modelini CustomUserAdmin ile
admin.site.register(User, CustomUserAdmin)
