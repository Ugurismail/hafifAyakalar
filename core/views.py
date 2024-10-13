from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect,get_object_or_404
from .forms import SignupForm, LoginForm,QuestionForm
from django.contrib.auth.decorators import login_required
from .forms import InvitationForm, User, AnswerForm
from .models import Invitation, UserProfile, Question, Answer
from django.contrib import messages
from django.db import transaction
from .models import Message
from .forms import MessageForm
from django.http import JsonResponse
import json
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse




def home(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        following_users = user_profile.following.all()
        following_questions = Question.objects.filter(user__userprofile__in=following_users).order_by('-created_at')
    else:
        following_questions = Question.objects.none()

    all_questions = Question.objects.all().order_by('-created_at')

    return render(request, 'core/home.html', {
        'all_questions': all_questions,
        'following_questions': following_questions,
    })

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            invitation_code = form.cleaned_data['invitation_code']
            # Validate the invitation code
            try:
                invitation = Invitation.objects.get(code=invitation_code, is_used=False)
            except Invitation.DoesNotExist:
                messages.error(request, 'Geçersiz veya kullanılmış davet kodu.')
                return render(request, 'core/signup.html', {'form': form})

            user = form.save()

            # Mark the invitation as used and link it to the user
            invitation.is_used = True
            invitation.used_by = user
            invitation.save()

            # Assign invitation quota to the new user
            user_profile = user.userprofile
            user_profile.invitation_quota = invitation.quota_granted
            user_profile.save()

            login(request, user)
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def send_invitation(request):
    user_profile = request.user.userprofile
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            quota_granted = form.cleaned_data['quota_granted']
            if user_profile.invitation_quota >= quota_granted:
                with transaction.atomic():
                    # Davet kodunu oluştur
                    invitation = form.save(commit=False)
                    invitation.sender = request.user
                    invitation.quota_granted = quota_granted
                    invitation.save()

                    # Kullanıcının davet hakkını düşür
                    user_profile.invitation_quota -= quota_granted
                    user_profile.save()

                # Oluşturulan kodu ve güncel davet hakkını şablona aktar
                return render(request, 'core/send_invitation.html', {
                    'form': InvitationForm(),  # Yeni davetler için boş form
                    'invitation_code': invitation.code,
                    'quota_granted': quota_granted,
                    'invitation_quota': user_profile.invitation_quota,
                })
            else:
                messages.error(request, 'Yeterli davet hakkınız yok.')
    else:
        form = InvitationForm()

    return render(request, 'core/send_invitation.html', {
        'form': form,
        'invitation_quota': user_profile.invitation_quota,
    })

@login_required
def profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    invitation_tree = []
    if user.is_superuser:
        invitation_tree = get_invitation_tree(user)
    return render(request, 'core/profile.html', {'user_profile': user_profile, 'invitation_tree': invitation_tree})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile_user.userprofile
    followers_count = user_profile.followers.count()
    following_count = user_profile.following.count()
    return render(request, 'core/user_profile.html', {
        'profile_user': profile_user,
        'followers_count': followers_count,
        'following_count': following_count
    })

def get_invitation_tree(user):
    invitations = Invitation.objects.filter(sender=user)
    tree = []
    for invite in invitations:
        if invite.is_used and invite.used_by:
            invited_user = invite.used_by
            subtree = get_invitation_tree(invited_user)
            tree.append({'user': invited_user, 'children': subtree})
        else:
            tree.append({'code': invite.code, 'children': []})
    return tree

@login_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question_text']
            answer_text = form.cleaned_data['answer_text']

            # Soruyu kaydet
            question = Question.objects.create(
                question_text=question_text,
                user=request.user
            )

            # Yanıtı kaydet
            Answer.objects.create(
                question=question,
                answer_text=answer_text,
                user=request.user
            )

            return redirect('home')
    else:
        form = QuestionForm()
    return render(request, 'core/add_question.html', {'form': form})

def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = question.answers.all()
    answer_form = AnswerForm()
    return render(request, 'core/question_detail.html', {
        'question': question,
        'answers': answers,
        'form': answer_form
    })

@login_required
def add_answer(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.user = request.user
            answer.save()
            return redirect('question_detail', question_id=question.id)
    else:
        form = AnswerForm()
    return render(request, 'core/add_answer.html', {'form': form, 'question': question})


@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'core/sent_messages.html', {'messages': messages})

@login_required
def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.recipient != request.user and message.sender != request.user:
        return redirect('inbox')
    if message.recipient == request.user:
        message.is_read = True
        message.save()
    return render(request, 'core/view_message.html', {'message': message})

@login_required
def get_conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    messages = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')

    # Mesajları okundu olarak işaretleyin
    messages.filter(recipient=request.user, is_read=False).update(is_read=True)

    messages_data = [
        {
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'body': msg.body,
            'timestamp': msg.timestamp.strftime('%d/%m/%Y %H:%M')
        }
        for msg in messages
    ]
    return JsonResponse({'messages': messages_data})



@login_required
def send_message_ajax(request):
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient_username')
        body = request.POST.get('body')
        recipient = get_object_or_404(User, username=recipient_username)
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            body=body
        )
        return JsonResponse({
            'sender': request.user.username,
            'body': message.body,
            'timestamp': message.timestamp.strftime('%d/%m/%Y %H:%M')
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id)  # Exclude the current user
    return render(request, 'core/user_list.html', {'users': users})

@login_required
def conversations(request):
    # Kullanıcının konuştuğu diğer kullanıcıları listeleyelim
    messages = Message.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('-timestamp')
    users = set()
    for message in messages:
        if message.sender != request.user:
            users.add(message.sender)
        if message.recipient != request.user:
            users.add(message.recipient)
    return render(request, 'core/conversations.html', {'users': users})


@login_required
def check_new_messages(request):
    last_check = request.session.get('last_message_check')
    now = timezone.now()
    if last_check:
        last_check = timezone.datetime.fromisoformat(last_check)
    else:
        last_check = now
    # Son kontrol zamanını güncelle
    request.session['last_message_check'] = now.isoformat()

    new_messages = Message.objects.filter(
        recipient=request.user,
        timestamp__gt=last_check
    ).order_by('timestamp')

    messages_data = [
        {
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'body': msg.body,
            'timestamp': msg.timestamp.strftime('%d/%m/%Y %H:%M')
        }
        for msg in new_messages
    ]
    return JsonResponse({'new_messages': messages_data})


@login_required
def get_unread_message_count(request):
    count = Message.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})

@login_required
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)
    user_profile = request.user.userprofile
    target_profile = target_user.userprofile
    user_profile.following.add(target_profile)
    return redirect('user_profile', username=username)

@login_required
def unfollow_user(request, username):
    target_user = get_object_or_404(User, username=username)
    user_profile = request.user.userprofile
    target_profile = target_user.userprofile
    user_profile.following.remove(target_profile)
    return redirect('user_profile', username=username)


def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []

    # Kullanıcıları ara
    users = User.objects.filter(username__icontains=query)
    for user in users:
        suggestions.append({
            'label': '@' + user.username,
            'url': reverse('user_profile', args=[user.username])
        })

    # Soruları ara
    questions = Question.objects.filter(question_text__icontains=query)
    for question in questions:
        suggestions.append({
            'label': question.question_text,
            'url': reverse('question_detail', args=[question.id])
        })

    return JsonResponse({'suggestions': suggestions})

def search(request):
    query = request.GET.get('q', '')
    if query:
        # Kullanıcıyı veya soruyu arayalım
        users = User.objects.filter(username__iexact=query.lstrip('@'))
        questions = Question.objects.filter(question_text__iexact=query)

        if users.exists():
            return redirect('user_profile', username=users.first().username)
        elif questions.exists():
            return redirect('question_detail', question_id=questions.first().id)
        else:
            # Aranan şey bulunamadı, yeni başlık oluşturma sayfasına yönlendirelim
            return render(request, 'core/new_topic.html', {'query': query})
    else:
        # Boş arama, ana sayfaya yönlendirelim
        return redirect('home')

@login_required
def add_question_from_search(request):
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        answer_text = request.POST.get('answer_text')

        # Soruyu oluştur
        question = Question.objects.create(
            question_text=question_text,
            user=request.user
        )

        # Yanıtı oluştur
        Answer.objects.create(
            question=question,
            answer_text=answer_text,
            user=request.user
        )

        return redirect('question_detail', question_id=question.id)
    else:
        return redirect('home')

def get_user_id(request, username):
    try:
        user = User.objects.get(username=username)
        return JsonResponse({'user_id': user.id})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    

