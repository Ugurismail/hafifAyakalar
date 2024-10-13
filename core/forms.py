# core/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from .models import Invitation, UserProfile,Question,Answer
from .models import Message


class SignupForm(UserCreationForm):
    invitation_code = forms.UUIDField(label='Davet Kodu', required=True)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'invitation_code')

class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, required=True, label='Kullanıcı Adı')
    password = forms.CharField(label='Şifre', widget=forms.PasswordInput)

class InvitationForm(forms.ModelForm):
    quota_granted = forms.IntegerField(label='Davet Hakkı Sayısı', min_value=1)

    class Meta:
        model = Invitation
        fields = ['quota_granted']

class QuestionForm(forms.ModelForm):
    answer_text = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Yanıtınızı buraya yazın'}),
        label='Yanıt',
        required=True
    )

    class Meta:
        model = Question
        fields = ['question_text', 'answer_text']
        labels = {
            'question_text': 'Soru',
        }
class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Message
        fields = ['recipient', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
        }