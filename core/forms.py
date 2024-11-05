# core/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from .models import Invitation, UserProfile,Question,Answer
from .models import Message


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['photo']





class SignupForm(UserCreationForm):
    invitation_code = forms.UUIDField(label='Davet Kodu', required=True)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'invitation_code')

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        required=True,
        label='Kullanıcı Adı',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Şifre',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class InvitationForm(forms.ModelForm):
    quota_granted = forms.IntegerField(label='Davet Hakkı Sayısı', min_value=1)

    class Meta:
        model = Invitation
        fields = ['quota_granted']

class QuestionForm(forms.ModelForm):
    answer_text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Yanıtınızı buraya yazın'}),
        required=False
    )

    class Meta:
        model = Question
        fields = ['question_text', 'answer_text']
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soru metni girin'}),
        }

    def __init__(self, *args, **kwargs):
        exclude_parent_questions = kwargs.pop('exclude_parent_questions', False)
        super(QuestionForm, self).__init__(*args, **kwargs)
        if exclude_parent_questions:
            self.fields.pop('parent_questions', None)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control'})

class StartingQuestionForm(forms.ModelForm):
    # Aynı anda hem soru hem de cevap eklemek için alanlar
    answer_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Yanıtınızı buraya yazın'}))

    class Meta:
        model = Question
        fields = ['question_text']  # Yalnızca soru başlığı ekleniyor
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soru başlığı'}),
        }

    def __init__(self, *args, **kwargs):
        super(StartingQuestionForm, self).__init__(*args, **kwargs)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control'})


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        widgets = {
            'answer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Yanıtınızı buraya yazın'}),
        }

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