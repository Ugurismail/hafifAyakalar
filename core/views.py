from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect,get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from .forms import InvitationForm, User, AnswerForm, StartingQuestionForm,SignupForm, LoginForm,QuestionForm,ProfilePhotoForm
from .models import Invitation, UserProfile, Question, Answer, StartingQuestion, Vote, Message, SavedItem,PinnedEntry
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
import json, random
from django.db.models import Q, Count, Max, F, ExpressionWrapper, IntegerField
from django.utils import timezone
from django.core.paginator import Paginator
from collections import defaultdict, Counter
import colorsys, re, json
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers import serialize
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType





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
    user_profile = user.userprofile

    # Kullanıcının soruları ve yanıtları
    questions = Question.objects.filter(user=user)
    answers = Answer.objects.filter(user=user)

    # Takipçi ve takip edilen sayıları
    follower_count = user_profile.followers.count()
    following_count = user_profile.following.count()

    # Sabitlenmiş giriş (pinned_entry)
    try:
        pinned_entry = PinnedEntry.objects.get(user=user)
    except PinnedEntry.DoesNotExist:
        pinned_entry = None

    # En çok kullanılan kelimeler
    top_words = get_top_words(user)

    context = {
        'profile_user': user,
        'user_profile': user_profile,
        'questions': questions,
        'answers': answers,
        'follower_count': follower_count,
        'following_count': following_count,
        'pinned_entry': pinned_entry,
        'top_words': top_words,
    }
    return render(request, 'core/profile.html', context)

def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile_user.userprofile

    # Kullanıcının soruları ve yanıtları
    questions = Question.objects.filter(user=profile_user)
    answers = Answer.objects.filter(user=profile_user)

    # Takipçi ve takip edilen sayıları
    follower_count = user_profile.followers.count()
    following_count = user_profile.following.count()

    # Kullanıcının takip edip etmediğini kontrol et
    if request.user.is_authenticated:
        is_following = request.user.userprofile.following.filter(user=profile_user).exists()
    else:
        is_following = False


    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'questions': questions,
        'answers': answers,
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following,
        'pinned_entry': pinned_entry,
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

@login_required
def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = question.answers.all()
    
    # **Form Oluşturma ve İşleme Bölümü**
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


    # Kullanıcının bu soruyu kaydedip kaydetmediğini kontrol et
    content_type_question = ContentType.objects.get_for_model(Question)
    user_has_saved_question = SavedItem.objects.filter(
        user=request.user,
        content_type=content_type_question,
        object_id=question.id
    ).exists()
    
    # Soru için kaydedilme sayısını al
    question_save_count = SavedItem.objects.filter(
        content_type=content_type_question,
        object_id=question.id
    ).count()
    
    # Kullanıcının oylarını al
    content_type_answer = ContentType.objects.get_for_model(Answer)
    user_votes = Vote.objects.filter(
        user=request.user,
        content_type=content_type_answer,
        object_id__in=answers.values_list('id', flat=True)
    ).values('object_id', 'value')
    user_vote_dict = {vote['object_id']: vote['value'] for vote in user_votes}
    
    # Her yanıta `user_vote_value` özelliğini ekle
    for answer in answers:
        answer.user_vote_value = user_vote_dict.get(answer.id, 0)
    
    # Kullanıcının kaydettiği yanıtların ID'lerini al
    saved_answer_ids = SavedItem.objects.filter(
        user=request.user,
        content_type=content_type_answer,
        object_id__in=answers.values_list('id', flat=True)
    ).values_list('object_id', flat=True)
    
    # Yanıtların kaydedilme sayılarını al
    answer_save_counts = SavedItem.objects.filter(
        content_type=content_type_answer,
        object_id__in=answers.values_list('id', flat=True)
    ).values('object_id').annotate(count=Count('id'))
    answer_save_dict = {item['object_id']: item['count'] for item in answer_save_counts}
    
    context = {
        'question': question,
        'answers': answers,
        'form': form,
        'user_has_saved_question': user_has_saved_question,
        'question_save_count': question_save_count,
        'saved_answer_ids': list(saved_answer_ids),
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
def vote(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = request.POST.get('object_id')
        value = request.POST.get('value')

        if not content_type or not object_id or not value:
            return JsonResponse({'error': 'Missing data'}, status=400)

        try:
            content_type_obj = ContentType.objects.get(model=content_type)
            model_class = content_type_obj.model_class()
            obj = model_class.objects.get(id=object_id)
        except (ContentType.DoesNotExist, model_class.DoesNotExist):
            return JsonResponse({'error': 'Invalid content_type or object_id'}, status=400)

        value = int(value)
        if value not in [1, -1]:
            return JsonResponse({'error': 'Invalid vote value'}, status=400)

        # Get or create the vote
        vote_obj, created = Vote.objects.get_or_create(
            user=request.user,
            content_type=content_type_obj,
            object_id=object_id,
            defaults={'value': value}
        )
        if not created:
            if vote_obj.value == value:
                # Remove the vote if it's the same
                vote_obj.delete()
                value = 0
            else:
                # Update the vote value
                vote_obj.value = value
                vote_obj.save()

        # Recalculate total upvotes and downvotes
        upvotes = Vote.objects.filter(content_type=content_type_obj, object_id=object_id, value=1).count()
        downvotes = Vote.objects.filter(content_type=content_type_obj, object_id=object_id, value=-1).count()

        # Update the object's vote counts
        obj.upvotes = upvotes
        obj.downvotes = downvotes
        obj.save()

        return JsonResponse({
            'upvotes': upvotes,
            'downvotes': downvotes,
            'user_vote_value': value
        })
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


from django.views.decorators.http import require_POST

@login_required
def save_item(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = request.POST.get('object_id')

        if not content_type or not object_id:
            return JsonResponse({'error': 'Missing content_type or object_id'}, status=400)

        try:
            content_type_obj = ContentType.objects.get(model=content_type)
        except ContentType.DoesNotExist:
            return JsonResponse({'error': 'Invalid content_type'}, status=400)

        # Daha önce kaydedilmiş mi kontrol edin
        existing_item = SavedItem.objects.filter(
            user=request.user,
            content_type=content_type_obj,
            object_id=object_id
        ).first()

        if existing_item:
            # Eğer kaydedilmişse, kaydı silerek "kaydetmeyi kaldır" işlemi yapın
            existing_item.delete()
            # Kaydedilme sayısını alın
            save_count = SavedItem.objects.filter(
                content_type=content_type_obj,
                object_id=object_id
            ).count()
            return JsonResponse({'status': 'unsaved', 'save_count': save_count})
        else:
            # Yeni bir kayıt oluşturun
            saved_item = SavedItem.objects.create(
                user=request.user,
                content_type=content_type_obj,
                object_id=object_id
            )
            # Kaydedilme sayısını alın
            save_count = SavedItem.objects.filter(
                content_type=content_type_obj,
                object_id=object_id
            ).count()
            return JsonResponse({'status': 'saved', 'save_count': save_count})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

def site_statistics(request):
    # Toplam kullanıcı sayısı (en az bir soru veya yanıt yazmış olanlar)
    user_count = User.objects.filter(
        Q(question__isnull=False) | Q(answer__isnull=False)
    ).distinct().count()

    # Toplam soru ve yanıt sayısı
    total_questions = Question.objects.count()
    total_answers = Answer.objects.count()

    # Toplam beğeni ve beğenmeme sayısı
    total_likes = Vote.objects.filter(value=1).count()
    total_dislikes = Vote.objects.filter(value=-1).count()

    # En çok soru soran kullanıcılar
    top_question_users = User.objects.annotate(
        question_count=Count('question')
    ).order_by('-question_count')[:5]

    # En çok yanıt veren kullanıcılar
    top_answer_users = User.objects.annotate(
        answer_count=Count('answer')
    ).order_by('-answer_count')[:5]

    # En çok oy alan sorular (upvotes - downvotes)
    top_voted_questions = Question.objects.annotate(
        total_votes=F('upvotes') - F('downvotes')
    ).order_by('-total_votes')[:5]

    # En çok beğenilen sorular (sadece upvotes)
    top_liked_questions = Question.objects.annotate(
        like_count=F('upvotes')
    ).order_by('-like_count')[:5]

    # En çok beğenilmeyen sorular (sadece downvotes)
    top_disliked_questions = Question.objects.annotate(
        dislike_count=F('downvotes')
    ).order_by('-dislike_count')[:5]

    # En çok oy alan yanıtlar (upvotes - downvotes)
    top_voted_answers = Answer.objects.annotate(
        total_votes=F('upvotes') - F('downvotes')
    ).order_by('-total_votes')[:5]

    # En çok beğenilen yanıtlar (sadece upvotes)
    top_liked_answers = Answer.objects.annotate(
        like_count=F('upvotes')
    ).order_by('-like_count')[:5]

    # En çok beğenilmeyen yanıtlar (sadece downvotes)
    top_disliked_answers = Answer.objects.annotate(
        dislike_count=F('downvotes')
    ).order_by('-dislike_count')[:5]

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

    # Metinleri birleştir ve küçük harfe çevir
    all_texts = ' '.join(question_texts) + ' ' + ' '.join(answer_texts)
    all_texts = all_texts.lower()

    # Kelimeleri ayıkla
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
        search_word_count = word_counts.get(search_word, 0)

    context = {
        'user_count': user_count,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'total_likes': total_likes,
        'total_dislikes': total_dislikes,
        'top_question_users': top_question_users,
        'top_answer_users': top_answer_users,
        'top_voted_questions': top_voted_questions,
        'top_liked_questions': top_liked_questions,
        'top_disliked_questions': top_disliked_questions,
        'top_voted_answers': top_voted_answers,
        'top_liked_answers': top_liked_answers,
        'top_disliked_answers': top_disliked_answers,
        'top_saved_questions': top_saved_questions,
        'top_saved_answers': top_saved_answers,
        'top_words': top_words,
        'search_word_count': search_word_count,
        'search_word': search_word,
        'exclude_words': ', '.join(sorted(exclude_words)),
        'exclude_words_input': exclude_words_input,
    }

    return render(request, 'core/site_statistics.html', context)

from django.contrib.contenttypes.models import ContentType

def user_homepage(request):
    if not request.user.is_authenticated:
        return redirect('signup')
    
    # Tüm soruları al
    all_questions = Question.objects.annotate(
        answers_count=Count('answers'),
        latest_answer_date=Max('answers__created_at')
    ).order_by(F('latest_answer_date').desc(nulls_last=True))
    
    # Başlangıç sorularını al
    starting_questions = StartingQuestion.objects.filter(user=request.user).annotate(
        total_subquestions=Count('question__subquestions'),
        latest_subquestion_date=Max('question__subquestions__created_at')
    ).order_by(F('latest_subquestion_date').desc(nulls_last=True))
    
    # Rastgele yanıtları alıyoruz
    random_items = Answer.objects.all().order_by('?')[:10]
    
    # Kullanıcının oylarını alalım
    if request.user.is_authenticated:
        content_type_answer = ContentType.objects.get_for_model(Answer)
        answer_votes = Vote.objects.filter(
            user=request.user,
            content_type=content_type_answer,
            object_id__in=random_items.values_list('id', flat=True)
        ).values('object_id', 'value')
        answer_vote_dict = {item['object_id']: item['value'] for item in answer_votes}
    
        # Her yanıta `user_vote_value` özelliğini ekle
        for answer in random_items:
            answer.user_vote_value = answer_vote_dict.get(answer.id, 0)
    else:
        # Kullanıcı giriş yapmamışsa, tüm oy değerlerini 0 olarak ayarla
        for answer in random_items:
            answer.user_vote_value = 0
    
    # Kullanıcının kaydettiği yanıtların ID'lerini al
    if request.user.is_authenticated:
        content_type_answer = ContentType.objects.get_for_model(Answer)
        saved_answer_ids = SavedItem.objects.filter(
            user=request.user,
            content_type=content_type_answer,
            object_id__in=random_items.values_list('id', flat=True)
        ).values_list('object_id', flat=True)
    else:
        saved_answer_ids = []
    
    # Yanıtların kaydedilme sayısını al
    content_type_answer = ContentType.objects.get_for_model(Answer)
    answer_save_counts = SavedItem.objects.filter(
        content_type=content_type_answer,
        object_id__in=random_items.values_list('id', flat=True)
    ).values('object_id').annotate(count=Count('id'))
    answer_save_dict = {item['object_id']: item['count'] for item in answer_save_counts}
    
    context = {
        'random_items': random_items,
        'saved_answer_ids': list(saved_answer_ids),
        'answer_save_dict': answer_save_dict,
        'all_questions': all_questions,
        'starting_questions': starting_questions,
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
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id, user=request.user)
    question_id = answer.question.id
    if request.method == 'POST':
        answer.delete()
        return redirect('user_homepage')
    else:
        return redirect('user_homepage')

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
    
def delete_question_and_subquestions(question):
    subquestions = question.subquestions.all()
    for sub in subquestions:
        delete_question_and_subquestions(sub)
    question.delete()


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

@login_required
@require_POST
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)
    request.user.userprofile.following.add(target_user.userprofile)
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def unfollow_user(request, username):
    target_user = get_object_or_404(User, username=username)
    request.user.userprofile.following.remove(target_user.userprofile)
    return JsonResponse({'status': 'success'})



@login_required
def pin_entry(request, entry_type, entry_id):
    if entry_type == 'question':
        question = get_object_or_404(Question, id=entry_id)
        # Mevcut bir PinnedEntry varsa, güncelle; yoksa oluştur
        pinned_entry, created = PinnedEntry.objects.get_or_create(user=request.user)
        pinned_entry.question = question
        pinned_entry.answer = None  # Yanıt yok
        pinned_entry.save()
    elif entry_type == 'answer':
        answer = get_object_or_404(Answer, id=entry_id)
        question = answer.question
        pinned_entry, created = PinnedEntry.objects.get_or_create(user=request.user)
        pinned_entry.question = question
        pinned_entry.answer = answer
        pinned_entry.save()
    else:
        # Geçersiz giriş türü
        return redirect('profile')
    return redirect('profile')


@login_required
def update_profile_photo(request):
    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil fotoğrafınız güncellendi.')
            return redirect('profile')
    else:
        form = ProfilePhotoForm(instance=request.user.userprofile)
    return render(request, 'core/update_profile_photo.html', {'form': form})


def get_top_words(user):
    answers = Answer.objects.filter(user=user)
    questions = Question.objects.filter(user=user)

    text = ' '.join([a.answer_text for a in answers] + [q.question_text for q in questions])
    words = re.findall(r'\w+', text.lower())
    word_counts = Counter(words)
    top_words = word_counts.most_common(10)

    return top_words