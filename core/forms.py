from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Invitation, UserProfile, Question, Answer, Message, RandomSentence
from django.core.validators import RegexValidator


username_with_spaces_validator = RegexValidator(
    regex=r'^[\w.@+\-_/ ]+$',  # Boşluk karakteri de eklendi
    message='Kullanıcı adı harf, rakam, @, ., +, -, _, / ve boşluk karakterleri içerebilir.'
)

class RandomSentenceForm(forms.ModelForm):
    class Meta:
        model = RandomSentence
        fields = ['sentence']
        widgets = {
            'sentence': forms.Textarea(attrs={
                'rows':2, 
                'class':'form-control', 
                'placeholder':'Yeni random cümlenizi girin (max 280 karakter)'
            })
        }
        labels = {
            'sentence': ''
        }

class SignupForm(forms.Form):
    username = forms.CharField(
        required=True,
        max_length=150,
        label='Kullanıcı Adı',
        validators=[username_with_spaces_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    invitation_code = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Şifre'
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        # Kendi validator'ınızı çalıştırıyorsunuz, model validator'ı yok artık.
        username_with_spaces_validator(username)
        return username

    def save(self):
        # Bu metot ile User modelini manuel oluşturuyoruz.
        user = User(username=self.cleaned_data['username'])
        user.set_password(self.cleaned_data['password'])
        user.save()
        return user

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
        if exclude_parent_questions and 'parent_questions' in self.fields:
            self.fields.pop('parent_questions', None)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control'})

class StartingQuestionForm(forms.ModelForm):
    answer_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Yanıtınızı buraya yazın'}))

    class Meta:
        model = Question
        fields = ['question_text']
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
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Mesajınızı buraya yazın',
                'style': 'resize: none; width: 100%;',
                'class': 'form-control',
            }),
        }

# Eksik olan ProfilePhotoForm tekrar tanımlanıyor.
class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['photo']
