from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect,get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from .forms import InvitationForm, User, AnswerForm, StartingQuestionForm,SignupForm, LoginForm,QuestionForm
from .models import Invitation, UserProfile, Question, Answer, StartingQuestion, Vote, Message, SavedItem
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
import json, random
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.core.paginator import Paginator
from collections import defaultdict, Counter
import colorsys, re, json
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers import serialize



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
            return redirect('user_homepage')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('user_homepage')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('user_homepage')

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
    context = {
        'user': user,
        'user_profile': user_profile,
        'invitation_tree': invitation_tree,
    }
    return render(request, 'core/profile.html', context)
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(UserProfile, user=profile_user)

    followers = user_profile.followers.all()
    following = user_profile.following.all()

    # Kullanıcı giriş yapmamışsa, 'user.userprofile' erişimi hata verebilir
    if request.user.is_authenticated:
        current_user_profile = request.user.userprofile
        is_following = current_user_profile.following.filter(user=profile_user).exists()
    else:
        is_following = False

    context = {
        'profile_user': profile_user,      # Profilini görüntülediğiniz kullanıcı
        'user_profile': user_profile,      # Kullanıcının profili
        'followers': followers,
        'following': following,
        'is_following': is_following,      # Takip edip etmediğinizi belirten değişken
    }
    return render(request, 'core/user_profile.html', context)

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

def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = Answer.objects.filter(question=question)
    saved_answer_ids = request.user.userprofile.saved_answers.values_list('id', flat=True) if request.user.is_authenticated else []
    answer_save_dict = {}  # Yanıtların kaydedilme sayıları
    for answer in answers:
        answer_save_dict[answer.id] = answer.saved_by.count()
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            new_answer = form.save(commit=False)
            new_answer.user = request.user
            new_answer.question = question
            new_answer.save()
            return redirect('question_detail', question_id=question.id)
    else:
        form = AnswerForm()
    context = {
        'question': question,
        'answers': answers,
        'form': form,
        'saved_answer_ids': saved_answer_ids,
        'answer_save_dict': answer_save_dict,
    }
    return render(request, 'core/question_detail.html', context)

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
            'url': reverse('user_profile', args=[user.username])  # Burada user.username kullanılıyor
        })

    # Soruları ara
    questions = Question.objects.filter(question_text__icontains=query)
    for question in questions:
        suggestions.append({
            'label': question.question_text,
            'url': reverse('question_detail', args=[question.id])
        })

    # Gelen veriyi sunucu konsoluna yazdırın
    import json
    print('search_suggestions verisi:', json.dumps({'suggestions': suggestions}, indent=4))

    return JsonResponse({'suggestions': suggestions})

@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    if query:
        questions = Question.objects.filter(question_text__icontains=query)
        users = User.objects.filter(username__icontains=query)
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
        if is_ajax:
            # AJAX isteği ise JSON formatında yanıt dön
            results = []
            for question in questions:
                results.append({
                    'type': 'question',
                    'id': question.id,
                    'text': question.question_text,
                    'url': reverse('question_detail', args=[question.id]),
                })
            for user in users:
                results.append({
                    'type': 'user',
                    'id': user.id,
                    'username': user.username,  # username alanını ekliyoruz
                    'text': '@' + user.username,
                    'url': reverse('user_profile', args=[user.username]),
                })
            return JsonResponse({'results': results})
        else:
            # Normal arama sonuçları sayfasını render et
            context = {'questions': questions, 'users': users, 'query': query}
            return render(request, 'core/search_results.html', context)
    else:
        return render(request, 'core/search_results.html', {})
@login_required
def add_question_from_search(request):
    query = request.GET.get('q', '').strip()
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid():
            # Yeni soru oluştur
            question = Question.objects.create(
                question_text=query,
                user=request.user,
                from_search=True  # Eğer modelinizde bu alan varsa
            )
            # Kullanıcıyı soru ile ilişkilendir
            question.users.add(request.user)
            # Yeni yanıt oluştur
            answer = answer_form.save(commit=False)
            answer.user = request.user
            answer.question = question
            answer.save()
            return redirect('question_detail', question_id=question.id)
    else:
        answer_form = AnswerForm()
    return render(request, 'core/add_question_from_search.html', {
        'query': query,
        'answer_form': answer_form
    })

def get_user_id(request, username):
    try:
        user = User.objects.get(username=username)
        return JsonResponse({'user_id': user.id})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
@login_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question_text']
            # Aynı soru metni varsa mevcut olanı kullan
            question, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            question.users.add(request.user)
            question.save()
            # Başlangıç sorusu olarak ekle
            StartingQuestion.objects.create(user=request.user, question=question)
            # Yanıtı kaydet
            Answer.objects.create(
                question=question,
                user=request.user,
                answer_text=form.cleaned_data.get('answer_text', '')
            )
            return redirect('user_homepage')
    else:
        form = QuestionForm()
    return render(request, 'core/add_question.html', {'form': form})

@login_required
def add_subquestion(request, question_id):
    parent_question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            subquestion_text = form.cleaned_data['question_text']
            answer_text = form.cleaned_data.get('answer_text', '')
            # Yeni veya mevcut alt soruyu oluştururken 'user' bilgisini ekliyoruz
            subquestion, created = Question.objects.get_or_create(
                question_text=subquestion_text,
                defaults={'user': request.user}
            )
            subquestion.users.add(request.user)
            parent_question.subquestions.add(subquestion)
            # Yanıtı kaydet
            Answer.objects.create(
                question=subquestion,
                user=request.user,
                answer_text=answer_text
            )
            messages.success(request, 'Alt soru başarıyla eklendi.')
            return redirect('question_detail', question_id=subquestion.id)
    else:
        form = QuestionForm()
    context = {
        'form': form,
        'parent_question': parent_question,
    }
    return render(request, 'core/add_subquestion.html', context)

@login_required
def question_detail(request, question_id):
    # Retrieve question and related data
    question = get_object_or_404(Question, id=question_id)
    
    answers_list = Answer.objects.filter(question=question).order_by('created_at')
    subquestions = question.subquestions.all()

    # Paginate answers
    paginator = Paginator(answers_list, 5)  # 5 answers per page
    page_number = request.GET.get('page')
    answers_page_obj = paginator.get_page(page_number)

    # Check if the user has saved the question
    user_has_saved_question = SavedItem.objects.filter(user=request.user, question=question).exists()

    # Count how many times the question has been saved
    question_save_count = SavedItem.objects.filter(question=question).count()

    # Get save counts for paginated answers
    # We need to adjust 'answer_id' to 'answer__id' in the values()
    answer_save_counts = SavedItem.objects.filter(answer__in=answers_page_obj).values('answer__id').annotate(count=Count('id'))
    answer_save_dict = {item['answer__id']: item['count'] for item in answer_save_counts}

    # Get IDs of answers saved by the user
    saved_answer_ids = SavedItem.objects.filter(user=request.user, answer__in=answers_page_obj).values_list('answer__id', flat=True)

    # Answer form
    form = AnswerForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            answer = form.save(commit=False)
            answer.user = request.user
            answer.question = question
            answer.save()
            messages.success(request, 'Yanıtınız başarıyla eklendi.')
            return redirect('question_detail', question_id=question.id)

    context = {
        'question': question,
        'answers': answers_page_obj,  # Use paginated answers here
        'subquestions': subquestions,
        'form': form,
        'user_has_saved_question': user_has_saved_question,
        'saved_answer_ids': list(saved_answer_ids),
        'answer_save_dict': answer_save_dict,
        'question_save_count': question_save_count,
    }
    return render(request, 'core/question_detail.html', context)

@login_required
def question_map(request):
    question_id = request.GET.get('question_id', None)
    questions = Question.objects.filter(from_search=False)
    nodes = {}
    links = []
    question_text_to_ids = defaultdict(list)

    # Build nodes dictionary keyed by question_text
    for question in questions:
        key = question.question_text
        question_text_to_ids[key].append(question.id)
        if key not in nodes:
            associated_users = list(question.users.all())
            user_ids = [user.id for user in associated_users]
            node = {
                "id": f"q{hash(key)}",  # Unique ID based on question_text
                "label": question.question_text,
                "users": user_ids,
                "size": 20 + 10 * (len(user_ids) - 1),
                "color": '',
                "question_id": question.id,  # Store a valid question ID
                "question_ids": [question.id],  # List of question IDs with same text
            }
            # Assign color based on user IDs
            if len(user_ids) == 1:
                node["color"] = get_user_color(user_ids[0])
            elif len(user_ids) > 1:
                node["color"] = '#CCCCCC'  # Grey for multiple users
            else:
                node["color"] = '#000000'  # Black if no user
            nodes[key] = node
        else:
            # Merge user IDs and update size
            existing_node = nodes[key]
            new_user_ids = [user.id for user in question.users.all()]
            combined_user_ids = list(set(existing_node["users"] + new_user_ids))
            existing_node["users"] = combined_user_ids
            existing_node["size"] = 20 + 5 * (len(combined_user_ids) - 1)
            existing_node["question_ids"].append(question.id)
            # Update color
            if len(combined_user_ids) == 1:
                existing_node["color"] = get_user_color(combined_user_ids[0])
            elif len(combined_user_ids) > 1:
                existing_node["color"] = '#CCCCCC'
            else:
                existing_node["color"] = '#000000'

    # Build links using question_text as keys
    link_set = set()
    for question in questions:
        source_key = question.question_text
        for subquestion in question.subquestions.all():
            target_key = subquestion.question_text
            if target_key in nodes:
                link_id = (nodes[source_key]["id"], nodes[target_key]["id"])
                if link_id not in link_set:
                    links.append({
                        "source": nodes[source_key]["id"],
                        "target": nodes[target_key]["id"]
                    })
                    link_set.add(link_id)

    question_nodes = {
        "nodes": list(nodes.values()),
        "links": links
    }
    return render(request, 'core/question_map.html', {
        'question_nodes': json.dumps(question_nodes),
        'focus_question_id': question_id,
    })

def get_user_color(user_id):
    hue = (user_id * 137.508) % 360  # Altın açı
    rgb = colorsys.hsv_to_rgb(hue / 360, 0.5, 0.95)
    hex_color = '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
    return hex_color

def about(request):
    return render(request, 'core/about.html')

# core/views.py

@login_required
def user_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if 'reset' in request.POST:
            # Varsayılan değerlere dön
            profile.background_color = '#F5F5F5'
            profile.text_color = '#000000'
            profile.header_background_color = '#ffffff'
            profile.header_text_color = '#333333'
            profile.link_color = '#0d6efd'
            profile.link_hover_color = '#0056b3'
            profile.button_background_color = '#007bff'
            profile.button_hover_background_color = '#0056b3'
            profile.button_text_color = '#ffffff'
            profile.hover_background_color = '#f0f0f0'
            profile.icon_color = '#333333'
            profile.icon_hover_color = '#007bff'
            profile.answer_background_color = '#F5F5F5'
            profile.content_background_color = '#ffffff'
            profile.tab_background_color = '#f8f9fa'
            profile.tab_text_color = '#000000'
            profile.tab_active_background_color = '#ffffff'
            profile.tab_active_text_color = '#000000'
            profile.dropdown_text_color = '#333333'
            profile.dropdown_hover_background_color = '#f2f2f2'
            profile.dropdown_hover_text_color = '#0056b3'
            profile.nav_link_hover_color = '#007bff'
            profile.nav_link_hover_bg = 'rgba(0, 0, 0, 0.05)'
            profile.pagination_background_color = '#ffffff'
            profile.pagination_text_color = '#000000'
            profile.pagination_active_background_color = '#007bff'
            profile.pagination_active_text_color = '#ffffff'
            # Diğer renk alanlarını da varsayılan değerlere ayarlayın
            profile.save()
            messages.success(request, 'Renk ayarlarınız varsayılan değerlere döndürüldü.')
            return redirect('user_settings')
        else:
            # Formdan gelen değerleri kaydet
            profile.background_color = request.POST.get('background_color', '#F5F5F5')
            profile.text_color = request.POST.get('text_color', '#000000')
            profile.header_background_color = request.POST.get('header_background_color', '#ffffff')
            profile.header_text_color = request.POST.get('header_text_color', '#333333')
            profile.link_color = request.POST.get('link_color', '#0d6efd')
            profile.link_hover_color = request.POST.get('link_hover_color', '#0056b3')
            profile.button_background_color = request.POST.get('button_background_color', '#007bff')
            profile.button_hover_background_color = request.POST.get('button_hover_background_color', '#0056b3')
            profile.button_text_color = request.POST.get('button_text_color', '#ffffff')
            profile.hover_background_color = request.POST.get('hover_background_color', '#f0f0f0')
            profile.icon_color = request.POST.get('icon_color', '#333333')
            profile.icon_hover_color = request.POST.get('icon_hover_color', '#007bff')
            profile.answer_background_color = request.POST.get('answer_background_color', '#F5F5F5')
            profile.content_background_color = request.POST.get('content_background_color', '#ffffff')
            profile.tab_background_color = request.POST.get('tab_background_color', '#f8f9fa')
            profile.tab_text_color = request.POST.get('tab_text_color', '#000000')
            profile.tab_active_background_color = request.POST.get('tab_active_background_color', '#ffffff')
            profile.tab_active_text_color = request.POST.get('tab_active_text_color', '#000000')
            profile.dropdown_text_color = request.POST.get('dropdown_text_color', '#333333')
            profile.dropdown_hover_background_color = request.POST.get('dropdown_hover_background_color', '#f2f2f2')
            profile.dropdown_hover_text_color = request.POST.get('dropdown_hover_text_color', '#0056b3')
            profile.nav_link_hover_color = request.POST.get('nav_link_hover_color', '#007bff')
            profile.nav_link_hover_bg = request.POST.get('nav_link_hover_bg', 'rgba(0, 0, 0, 0.05)')
            profile.pagination_background_color = request.POST.get('pagination_background_color', '#ffffff')
            profile.pagination_text_color = request.POST.get('pagination_text_color', '#000000')
            profile.pagination_active_background_color = request.POST.get('pagination_active_background_color', '#007bff')
            profile.pagination_active_text_color = request.POST.get('pagination_active_text_color', '#ffffff')
            # Diğer renk alanlarını da kaydedin
            profile.save()
            messages.success(request, 'Renk ayarlarınız güncellendi.')
            return redirect('user_settings')
    return render(request, 'core/user_settings.html', {'user_profile': profile})


@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id, user=request.user)
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yanıt başarıyla güncellendi.')
            return redirect('question_detail', question_id=answer.question.id)
    else:
        form = AnswerForm(instance=answer)
    return render(request, 'core/edit_answer.html', {'form': form, 'answer': answer})

@login_required
def add_starting_question(request):
    if request.method == 'POST':
        form = StartingQuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question_text']
            question, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={'user': request.user}
            )
            question.users.add(request.user)
            question.save()
            StartingQuestion.objects.create(user=request.user, question=question)
            Answer.objects.create(
                question=question,
                user=request.user,
                answer_text=form.cleaned_data['answer_text']
            )
            return redirect('user_homepage')
    else:
        form = StartingQuestionForm()
    return render(request, 'core/add_starting_question.html', {'form': form})

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.method == 'POST':
        if request.user == question.user:
            with transaction.atomic():
                # Delete all answers associated with the question by the user
                Answer.objects.filter(question=question, user=request.user).delete()
                # Remove the user from the question's users
                question.users.remove(request.user)
                if question.users.count() == 0:
                    # If no users are associated, delete the question and its subquestions
                    delete_question_and_subquestions(question)
                    messages.success(request, 'Soru ve alt soruları başarıyla silindi.')
                else:
                    messages.success(request, 'Soru sizin için silindi.')
            return redirect('user_homepage')
        else:
            messages.error(request, 'Bu soruyu silme yetkiniz yok.')
            return redirect('question_detail', question_id=question.id)
    else:
        return render(request, 'core/confirm_delete_question.html', {'question': question})

@login_required
def vote(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = int(request.POST.get('object_id'))
        value = int(request.POST.get('value'))  # 1 veya -1

        if content_type == 'question':
            question = get_object_or_404(Question, id=object_id)
            with transaction.atomic():
                vote, created = Vote.objects.get_or_create(
                    user=request.user,
                    question=question,
                    defaults={'value': value}
                )
                if not created:
                    # Kullanıcı daha önce oy vermiş
                    if vote.value != value:
                        # Önceki oyu geri al
                        if vote.value == 1:
                            question.upvotes -= 1
                        elif vote.value == -1:
                            question.downvotes -= 1
                        # Yeni oyu ekle
                        vote.value = value
                        vote.save()
                        if value == 1:
                            question.upvotes += 1
                        elif value == -1:
                            question.downvotes += 1
                    else:
                        # Aynı oya tekrar basıldıysa, oy geri çekilir
                        if vote.value == 1:
                            question.upvotes -= 1
                        elif vote.value == -1:
                            question.downvotes -= 1
                        vote.delete()
                else:
                    # Yeni oy
                    if value == 1:
                        question.upvotes += 1
                    elif value == -1:
                        question.downvotes += 1
                question.save()
            return JsonResponse({'upvotes': question.upvotes, 'downvotes': question.downvotes})
        elif content_type == 'answer':
            answer = get_object_or_404(Answer, id=object_id)
            with transaction.atomic():
                vote, created = Vote.objects.get_or_create(
                    user=request.user,
                    answer=answer,
                    defaults={'value': value}
                )
                if not created:
                    if vote.value != value:
                        if vote.value == 1:
                            answer.upvotes -= 1
                        elif vote.value == -1:
                            answer.downvotes -= 1
                        vote.value = value
                        vote.save()
                        if value == 1:
                            answer.upvotes += 1
                        elif value == -1:
                            answer.downvotes += 1
                    else:
                        if vote.value == 1:
                            answer.upvotes -= 1
                        elif vote.value == -1:
                            answer.downvotes -= 1
                        vote.delete()
                else:
                    if value == 1:
                        answer.upvotes += 1
                    elif value == -1:
                        answer.downvotes += 1
                answer.save()
            return JsonResponse({'upvotes': answer.upvotes, 'downvotes': answer.downvotes})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def save_item(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = request.POST.get('object_id')

        if content_type == 'question':
            question = Question.objects.get(id=object_id)
            saved_item, created = SavedItem.objects.get_or_create(user=request.user, question=question)
            if not created:
                saved_item.delete()  # Zaten kayıtlıysa kaldır
                status = 'removed'
            else:
                status = 'saved'
            # Güncellenmiş kaydetme sayısını alın
            save_count = SavedItem.objects.filter(question=question).count()
            return JsonResponse({'status': status, 'save_count': save_count})
        elif content_type == 'answer':
            answer = Answer.objects.get(id=object_id)
            saved_item, created = SavedItem.objects.get_or_create(user=request.user, answer=answer)
            if not created:
                saved_item.delete()  # Zaten kayıtlıysa kaldır
                status = 'removed'
            else:
                status = 'saved'
            # Güncellenmiş kaydetme sayısını alın
            save_count = SavedItem.objects.filter(answer=answer).count()
            return JsonResponse({'status': status, 'save_count': save_count})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def site_statistics(request):
    # Mevcut istatistikler
    user_count = User.objects.filter(
        Q(questions__isnull=False) | Q(answers__isnull=False)
    ).distinct().count()
    total_questions = Question.objects.count()
    total_answers = Answer.objects.count()
    total_likes = Vote.objects.filter(value=1).count()
    total_dislikes = Vote.objects.filter(value=-1).count()

    # En çok soru soran kullanıcılar
    top_question_users = User.objects.annotate(
        question_count=Count('questions')
    ).order_by('-question_count')[:5]

    # En çok yanıt veren kullanıcılar
    top_answer_users = User.objects.annotate(
        answer_count=Count('answers')
    ).order_by('-answer_count')[:5]

    # En çok beğenilen sorular
    top_liked_questions = Question.objects.annotate(
        like_count=Count('vote', filter=Q(vote__value=1))
    ).order_by('-like_count')[:5]

    # En çok beğenilen yanıtlar
    top_liked_answers = Answer.objects.annotate(
        like_count=Count('vote', filter=Q(vote__value=1))
    ).order_by('-like_count')[:5]

    # En çok kaydedilen sorular
    top_saved_questions = Question.objects.annotate(
        save_count=Count('saveditem')
    ).order_by('-save_count')[:5]

    # En çok kaydedilen yanıtlar
    top_saved_answers = Answer.objects.annotate(
        save_count=Count('saveditem')
    ).order_by('-save_count')[:5]

    # Tüm soru ve yanıt metinlerini al
    question_texts = Question.objects.values_list('question_text', flat=True)
    answer_texts = Answer.objects.values_list('answer_text', flat=True)

    # Metinleri birleştir
    all_texts = ' '.join(question_texts) + ' ' + ' '.join(answer_texts)

    # Metinleri küçük harfe çevir ve özel karakterleri kaldır
    all_texts = all_texts.lower()
    words = re.findall(r'\b\w+\b', all_texts)

    # Kullanıcının hariç tutmak istediği kelimeleri al
    exclude_words_input = request.GET.get('exclude_words', '')
    if exclude_words_input:
        # Virgülle ayrılmış kelimeleri listeye çevir
        exclude_words_list = re.split(r',\s*', exclude_words_input.strip())
        exclude_words = set(word.lower() for word in exclude_words_list)
    else:
        exclude_words = set()

    # Kelimeleri filtrele
    filtered_words = [word for word in words if word not in exclude_words]

    # Kelime sıklıklarını hesapla
    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(10)

    # Kelime arama
    search_word = request.GET.get('search_word', '').strip().lower()
    search_word_count = None
    if search_word:
        search_word_count = word_counts.get(search_word.lower(), 0)

    context = {
        'user_count': user_count,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'total_likes': total_likes,
        'total_dislikes': total_dislikes,
        'top_question_users': top_question_users,
        'top_answer_users': top_answer_users,
        'top_liked_questions': top_liked_questions,
        'top_liked_answers': top_liked_answers,
        'top_saved_questions': top_saved_questions,
        'top_saved_answers': top_saved_answers,
        'top_words': top_words,
        'search_word_count': search_word_count,
        'search_word': search_word,
        'exclude_words': ', '.join(sorted(exclude_words)),
        'exclude_words_input': exclude_words_input,
    }

    return render(request, 'core/site_statistics.html', context)


def delete_question_and_subquestions(question):
    subquestions = question.subquestions.all()
    for sub in subquestions:
        delete_question_and_subquestions(sub)
    question.delete()

@login_required
def user_homepage(request):
    # All questions
    all_questions_list = Question.objects.annotate(
        answers_count=Count('answers'),
        latest_answer_date=Max('answers__created_at')
    ).annotate(
        last_activity=Coalesce('latest_answer_date', 'created_at')
    ).order_by('-last_activity')

    # Paginate all questions
    all_questions_paginator = Paginator(all_questions_list, 5)  # Sayfa başına 5 soru
    page_number = request.GET.get('page')
    all_questions_page_obj = all_questions_paginator.get_page(page_number)

    # Starting questions
    starting_questions_list = StartingQuestion.objects.filter(user=request.user)
    starting_questions_with_counts = [
        {
            'question': sq.question,
            'total_subquestions': sq.question.get_total_subquestions_count()
        }
        for sq in starting_questions_list
    ]

    # Paginate starting questions
    starting_questions_paginator = Paginator(starting_questions_with_counts, 5)
    starting_page_number = request.GET.get('starting_page')
    starting_questions_page_obj = starting_questions_paginator.get_page(starting_page_number)

    # Random answers
    random_items = random.sample(list(Answer.objects.select_related('question')), min(10, Answer.objects.count()))

    # User's saved answer IDs
    saved_answer_ids = SavedItem.objects.filter(user=request.user, answer__in=random_items).values_list('answer__id', flat=True)

    # Answer save counts
    answer_save_counts = SavedItem.objects.filter(answer__in=random_items).values('answer_id').annotate(count=Count('id'))
    answer_save_dict = {item['answer_id']: item['count'] for item in answer_save_counts}

    context = {
        'starting_questions': starting_questions_page_obj,
        'all_questions': all_questions_page_obj,  # Sayfalandırılmış all_questions
        'random_items': random_items,
        'saved_answer_ids': list(saved_answer_ids),
        'answer_save_dict': answer_save_dict,
    }
    return render(request, 'core/user_homepage.html', context)

@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id, user=request.user)
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yanıt başarıyla güncellendi.')
            return redirect('question_detail', question_id=answer.question.id)
    else:
        form = AnswerForm(instance=answer)
    return render(request, 'core/edit_answer.html', {'form': form, 'answer': answer})

@login_required
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id, user=request.user)
    if request.method == 'POST':
        answer.delete()
        messages.success(request, 'Yanıt başarıyla silindi.')
    else:
        messages.error(request, 'Yanıt silinemedi.')
    return redirect('question_detail', question_id=answer.question.id)

def delete_question_and_subquestions(question):
    subquestions = question.subquestions.all()
    for sub in subquestions:
        delete_question_and_subquestions(sub)
    question.delete()

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.method == 'POST':
        if request.user == question.user:
            with transaction.atomic():
                # Delete all answers associated with the question by the user
                Answer.objects.filter(question=question, user=request.user).delete()
                # Remove the user from the question's users
                question.users.remove(request.user)
                if question.users.count() == 0:
                    # If no users are associated, delete the question and its subquestions
                    delete_question_and_subquestions(question)
                    messages.success(request, 'Soru ve alt soruları başarıyla silindi.')
                else:
                    messages.success(request, 'Soru sizin için silindi.')
            return redirect('user_homepage')
        else:
            messages.error(request, 'Bu soruyu silme yetkiniz yok.')
            return redirect('question_detail', question_id=question.id)
    else:
        return render(request, 'core/confirm_delete_question.html', {'question': question})
    
@login_required
def single_answer(request, question_id, answer_id):
    question = get_object_or_404(Question, id=question_id)
    answer = get_object_or_404(Answer, id=answer_id, question=question)
    
    # Kullanıcının kaydettiği yanıtların ID'lerini al
    saved_answer_ids = SavedItem.objects.filter(user=request.user, answer=answer).values_list('answer__id', flat=True)
    
    # Yanıt için kaydedilme sayısını al
    answer_save_counts = SavedItem.objects.filter(answer=answer).values('answer_id').annotate(count=Count('id'))
    answer_save_dict = {item['answer_id']: item['count'] for item in answer_save_counts}
    
    context = {
        'question': question,
        'answers': [answer],
        'saved_answer_ids': list(saved_answer_ids),
        'answer_save_dict': answer_save_dict,
    }
    return render(request, 'core/single_answer.html', context)

def user_search(request):
    query = request.GET.get('q', '').strip()
    users = User.objects.filter(username__icontains=query)[:10]
    results = [{'id': user.id, 'username': user.username} for user in users]
    return JsonResponse({'results': results})

@login_required
def map_data(request):
    filter_param = request.GET.get('filter')
    user_ids = request.GET.getlist('user_id')

    if filter_param == 'me':
        # Giriş yapan kullanıcının soruları
        questions = Question.objects.filter(users=request.user, from_search=False)
    elif user_ids:
        # Seçili kullanıcıların soruları
        questions = Question.objects.filter(users__id__in=user_ids, from_search=False).distinct()
    else:
        # Tüm sorular
        questions = Question.objects.filter(from_search=False)

    question_nodes = generate_question_nodes(questions)

    return JsonResponse(question_nodes, safe=False)

def generate_question_nodes(questions):
    nodes = {}
    links = []
    question_text_to_ids = defaultdict(list)

    # Düğümleri oluştur
    for question in questions:
        key = question.question_text
        question_text_to_ids[key].append(question.id)
        if key not in nodes:
            associated_users = list(question.users.all())
            user_ids = [user.id for user in associated_users]
            node = {
                "id": f"q{hash(key)}",
                "label": question.question_text,
                "users": user_ids,
                "size": 20 + 10 * (len(user_ids) - 1),
                "color": '',
                "question_id": question.id,
                "question_ids": [question.id],
            }
            # Rengi belirle
            if len(user_ids) == 1:
                node["color"] = get_user_color(user_ids[0])
            elif len(user_ids) > 1:
                node["color"] = '#CCCCCC'  # Gri renk
            else:
                node["color"] = '#000000'  # Siyah
            nodes[key] = node
        else:
            # Kullanıcıları ve boyutu güncelle
            existing_node = nodes[key]
            new_user_ids = [user.id for user in question.users.all()]
            combined_user_ids = list(set(existing_node["users"] + new_user_ids))
            existing_node["users"] = combined_user_ids
            existing_node["size"] = 20 + 5 * (len(combined_user_ids) - 1)
            existing_node["question_ids"].append(question.id)
            # Rengi güncelle
            if len(combined_user_ids) == 1:
                existing_node["color"] = get_user_color(combined_user_ids[0])
            elif len(combined_user_ids) > 1:
                existing_node["color"] = '#CCCCCC'
            else:
                existing_node["color"] = '#000000'

    # Bağlantıları oluştur
    link_set = set()
    for question in questions:
        source_key = question.question_text
        for subquestion in question.subquestions.all():
            target_key = subquestion.question_text
            if target_key in nodes:
                link_id = (nodes[source_key]["id"], nodes[target_key]["id"])
                if link_id not in link_set:
                    links.append({
                        "source": nodes[source_key]["id"],
                        "target": nodes[target_key]["id"]
                    })
                    link_set.add(link_id)

    question_nodes = {
        "nodes": list(nodes.values()),
        "links": links
    }
    return question_nodes

@login_required
def mark_messages_as_read(request):
    if request.method == 'POST':
        sender_username = request.POST.get('sender_username')
        sender = get_object_or_404(User, username=sender_username)
        Message.objects.filter(sender=sender, recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def bkz_view(request, query):
    try:
        question = Question.objects.get(question_text__iexact=query)
        return redirect('question_detail', question_id=question.id)
    except Question.DoesNotExist:
        # Soru bulunamazsa, add_question_from_search sayfasına yönlendirin
        return redirect(f'{reverse("add_question_from_search")}?q={query}')

@login_required
def reference_search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        questions = Question.objects.filter(question_text__icontains=query)
        for question in questions:
            results.append({
                'id': question.id,
                'text': question.question_text
            })
    return JsonResponse({'results': results})
