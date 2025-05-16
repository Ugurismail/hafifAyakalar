from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Invitation, UserProfile, Question, Answer, Message, RandomSentence, Definition, Reference
from django.core.validators import RegexValidator
from .models import Poll, PollOption
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError

# Kullanıcı adında boşluklar ve Türkçe karakterlere izin veren validator
username_with_spaces_validator = RegexValidator(
    regex=r'^[\w.@+\-_/ \u00C0-\u017F]+$',
    message='Kullanıcı adı harf, rakam, @, ., +, -, _, /, boşluk ve Türkçe karakterleri içerebilir.'
)

class RandomSentenceForm(forms.ModelForm):
    class Meta:
        model = RandomSentence
        fields = ['sentence']
        widgets = {
            'sentence': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Yeni random cümlenizi girin (max 280 karakter)'
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
        username_with_spaces_validator(username)
        return username

    def save(self):
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
        widget=forms.Textarea(attrs={
            'class': 'form-control auto-expand',
            'rows': 4,
            'placeholder': 'Yanıtınızı buraya yazın'
        }),
        required=False
    )

    class Meta:
        model = Question
        fields = ['question_text', 'answer_text']
        widgets = {
            'question_text': forms.TextInput(attrs={
                'class': 'form-control auto-expand',
                'placeholder': 'Soru metni girin'
            }),
        }

    def __init__(self, *args, **kwargs):
        exclude_parent_questions = kwargs.pop('exclude_parent_questions', False)
        super(QuestionForm, self).__init__(*args, **kwargs)
        if exclude_parent_questions and 'parent_questions' in self.fields:
            self.fields.pop('parent_questions', None)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control'})

class StartingQuestionForm(forms.ModelForm):
    answer_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control auto-expand',
            'rows': 4,
            'placeholder': 'Yanıtınızı buraya yazın'
        })
    )

    class Meta:
        model = Question
        fields = ['question_text']
        widgets = {
            'question_text': forms.TextInput(attrs={
                'class': 'form-control auto-expand',
                'placeholder': 'Soru başlığı'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(StartingQuestionForm, self).__init__(*args, **kwargs)
        self.fields['question_text'].widget.attrs.update({'class': 'form-control '})

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        widgets = {
            # Otomatik genişleme özelliğini sağlayacak 'auto-expand' sınıfı eklenmiştir.
            'answer_text': forms.Textarea(attrs={
                'class': 'form-control auto-expand',
                'rows': 2,
                'placeholder': 'Yanıtınızı buraya yazın'
            }),
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

class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['photo']

class PollForm(forms.Form):
    question_text = forms.CharField(
        max_length=255, 
        label="Anket Sorusu",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Anket sorusunu giriniz'
        })
    )
    end_date = forms.DateTimeField(
        label="Bitiş Tarihi (YYYY-MM-DD HH:MM)",
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    )
    is_anonymous = forms.BooleanField(
        required=False, 
        initial=True, 
        label="Anonim Oy",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        for i in range(1, 11):
            self.fields[f'option_{i}'] = forms.CharField(
                required=False,
                max_length=255,
                label=f"Seçenek {i}",
                widget=forms.TextInput(attrs={
                    'class': 'form-control mb-2',
                    'placeholder': f'Seçenek {i}'
                })
            )

    def clean(self):
        cleaned_data = super().clean()
        end_date = cleaned_data.get('end_date')
        if end_date <= timezone.now():
            self.add_error('end_date', 'Bitiş tarihi gelecekte bir zaman olmalıdır.')
        if end_date and end_date > (timezone.now() + datetime.timedelta(days=365)):
            self.add_error('end_date', 'Bitiş tarihi 1 yıldan fazla olmamalıdır.')
        options = []
        for i in range(1, 11):
            opt = cleaned_data.get(f'option_{i}', '').strip()
            if opt:
                options.append(opt)
        if len(options) < 2:
            self.add_error('option_1', 'En az 2 seçenek girmelisiniz.')
        cleaned_data['options'] = options
        return cleaned_data

class DefinitionForm(forms.ModelForm):
    class Meta:
        model = Definition
        fields = ['definition_text']
        labels = {
            'definition_text': 'Tanım',
        }
        widgets = {
            'definition_text': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': '1000',
                'placeholder': 'En fazla 1000 karakterlik tanımınızı girin...'
            }),
        }

    def clean_definition_text(self):
        data = self.cleaned_data.get('definition_text', '').strip()
        if len(data) > 1000:
            raise ValidationError("Tanım 1000 karakterden uzun olamaz.")
        if not data:
            raise ValidationError("Tanım alanı boş olamaz.")
        return data

class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = [
            'author_surname',
            'author_name',
            'year',
            'metin_ismi',
            'rest',
            'abbreviation'
        ]
        labels = {
            'author_surname': 'Yazar Soyadı',
            'author_name': 'Yazar Adı',
            'year': 'Yıl',
            'metin_ismi': 'Metin İsmi',
            'rest': 'Künyenin Kalanı',
            'abbreviation': 'Kısaltma (Opsiyonel)',
        }
        widgets = {
            'author_surname': forms.TextInput(attrs={'class': 'form-control'}),
            'author_name': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'metin_ismi': forms.TextInput(attrs={'class': 'form-control'}),
            'rest': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': '2000'
            }),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year and (year < 1 or year > 9999):
            raise forms.ValidationError("Yıl 1 ile 9999 arasında olmalıdır.")
        return year

class AnswerEditForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        widgets = {
            'answer_text': forms.Textarea(attrs={'class': 'auto-expand form-control'}),
        }