from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django import forms

from core.models import (
    Invitation, UserProfile, Question, Answer, 
    Poll, PollOption, PollVote, SavedItem, Vote, PinnedEntry, 
    Entry, RandomSentence, Message, Definition, Reference
)

# =============================================================================
# 1) Standart Admin Kaydı (Invitation, UserProfile, SavedItem, Vote, PinnedEntry, Entry, RandomSentence)
# =============================================================================
admin.site.register(Invitation)
admin.site.register(UserProfile)
admin.site.register(SavedItem)
admin.site.register(Vote)
admin.site.register(PinnedEntry)
admin.site.register(Entry)
admin.site.register(RandomSentence)

# =============================================================================
# 2) Kullanıcı Admin – Mesaj Gönderme, Grupların Gösterimi ve Filtrelenmesi
# =============================================================================

# Mesaj gönderme formu
class MassMessageForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.HiddenInput)
    message_body = forms.CharField(
        label="Mesajınız",
        widget=forms.Textarea(attrs={"rows": 4, "cols": 60}),
        required=True
    )

# Custom UserAdmin: 
# - list_display’e "display_groups" ekleyip, kullanıcıya ait grupları virgülle gösteriyoruz.
# - list_filter’e "groups" ekleyerek filtreleme yapabiliyoruz.
# - Ayrıca, admin action ile seçili kullanıcılara mesaj gönderme işlevini de koruyoruz.
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('display_groups',)
    list_filter = UserAdmin.list_filter + ('groups',)
    
    def display_groups(self, obj):
        return ", ".join(g.name for g in obj.groups.all())
    display_groups.short_description = "Gruplar"

    actions = ["send_message_to_selected_users"]

    def get_urls(self):
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
        if not queryset.exists():
            self.message_user(request, "Hiç kullanıcı seçmediniz!", level=messages.WARNING)
            return
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return redirect(f"send-messages/?ids={','.join(selected)}")

    send_message_to_selected_users.short_description = "Seçili kullanıcılara mesaj gönder"

    def send_messages_intermediate(self, request):
        from core.models import Message
        ids_param = request.GET.get('ids', '')
        if not ids_param:
            self.message_user(request, "Kullanıcı seçilmedi veya geçersiz ID.", level=messages.ERROR)
            return redirect("..")
        user_ids = ids_param.split(',')
        selected_users = User.objects.filter(pk__in=user_ids)
        if request.method == 'POST':
            form = MassMessageForm(request.POST)
            if form.is_valid():
                message_body = form.cleaned_data['message_body']
                admin_user = request.user
                count = 0
                for user in selected_users:
                    if user != admin_user:
                        Message.objects.create(
                            sender=admin_user,
                            recipient=user,
                            body=message_body
                        )
                        count += 1
                self.message_user(request, f"{count} kullanıcıya mesaj gönderildi.")
                return redirect("/admin/auth/user/")
        else:
            initial_data = {'_selected_action': ids_param}
            form = MassMessageForm(initial=initial_data)
        return render(request, 'admin/send_message_form.html', {
            'form': form,
            'selected_users': selected_users,
        })

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# =============================================================================
# 3) Grup Admin – Mesaj Gönderme, Üye Listesi (Inline) ve Üyelerin Yönetimi
# =============================================================================

# Inline: Kullanıcı-Group ilişkisini yönetmek için User.groups.through modelini kullanıyoruz.
class UserGroupInline(admin.TabularInline):
    model = User.groups.through
    extra = 0
    verbose_name = "Üye"
    verbose_name_plural = "Üyeler"

# Grup mesajı gönderme formu
class GroupMassMessageForm(forms.Form):
    selected_action = forms.CharField(widget=forms.HiddenInput)
    message_body = forms.CharField(
        label="Mesajınız",
        widget=forms.Textarea(attrs={"rows": 4, "cols": 60}),
        required=True
    )

# Custom GroupAdmin: 
# - Grup listesinden seçili gruplara mesaj göndermek için admin action ekleniyor.
# - Değişim (change) sayfasında üye listesi inline olarak gösteriliyor, böylece üyeleri görüntüleyip çıkartabiliyoruz.
class CustomGroupAdmin(admin.ModelAdmin):
    actions = ["send_message_to_group"]
    inlines = [UserGroupInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-group-messages/',
                self.admin_site.admin_view(self.send_group_messages_intermediate),
                name='send_group_messages_intermediate',
            )
        ]
        return custom_urls + urls

    def send_message_to_group(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Hiç grup seçmediniz!", level=messages.WARNING)
            return
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return redirect(f"send-group-messages/?ids={','.join(selected)}")

    send_message_to_group.short_description = "Seçili gruplara mesaj gönder"

    def send_group_messages_intermediate(self, request):
        from core.models import Message
        ids_param = request.GET.get('ids', '')
        if not ids_param:
            self.message_user(request, "Grup seçilmedi veya geçersiz ID.", level=messages.ERROR)
            return redirect("..")
        group_ids = ids_param.split(',')
        selected_groups = Group.objects.filter(pk__in=group_ids)
        if request.method == "POST":
            form = GroupMassMessageForm(request.POST)
            if form.is_valid():
                message_body = form.cleaned_data["message_body"]
                users_set = set()
                for group in selected_groups:
                    for user in group.user_set.all():
                        users_set.add(user)
                count = 0
                for user in users_set:
                    Message.objects.create(
                        sender=request.user,
                        recipient=user,
                        body=message_body
                    )
                    count += 1
                self.message_user(request, f"{count} kullanıcıya mesaj gönderildi.")
                return redirect("/admin/auth/group/")
        else:
            initial_data = {'selected_action': ','.join(str(g.id) for g in selected_groups)}
            form = GroupMassMessageForm(initial=initial_data)
        return render(request, "admin/send_group_message.html", {
            "groups": selected_groups,
            "form": form,
            "title": "Seçili gruplara mesaj gönder"
        })

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

# =============================================================================
# 4) Soru, Yanıt, Anket ve Referans Admin Kayıtları
# =============================================================================
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

@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    search_fields = ['author_surname', 'author_name', 'year', 'rest', 'abbreviation']
    list_display = ['author_surname', 'author_name', 'year', 'abbreviation', 'short_rest']
    list_filter = ['year']

    def short_rest(self, obj):
        return (obj.rest[:50] + "...") if len(obj.rest) > 50 else obj.rest
    short_rest.short_description = "Ek Bilgiler (kısaltılmış)"

class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 0

@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ['question', 'user', 'created_at', 'get_answer']
    search_fields = ['definition_text', 'question__question_text', 'user__username']
    list_filter = ['created_at', 'user']

    def get_answer(self, obj):
        return obj.answer.answer_text if obj.answer else '-'
    get_answer.short_description = 'Yanıt'
