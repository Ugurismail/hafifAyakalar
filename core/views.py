from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from .forms import InvitationForm, AnswerForm, StartingQuestionForm, SignupForm, LoginForm, QuestionForm, ProfilePhotoForm, MessageForm
from .models import Invitation, UserProfile, Question, Answer, StartingQuestion, Vote, Message, SavedItem, PinnedEntry
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
import json, random
from django.db.models import Q, Count, Max, F, ExpressionWrapper, IntegerField, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from collections import defaultdict, Counter
import colorsys, re, json
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User  # User buradan import edilmeli
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers import serialize
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import RandomSentence
from .forms import RandomSentenceForm
from .models import Poll, PollOption, PollVote
from .forms import PollForm







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
            # Davetiye kodunu kontrol et
            try:
                invitation = Invitation.objects.get(code=invitation_code, is_used=False)
            except Invitation.DoesNotExist:
                messages.error(request, 'Geçersiz veya kullanılmış davet kodu.')
                return render(request, 'core/signup.html', {'form': form})

            user = form.save()  # Artık ModelForm yerine normal Form kullanıyoruz.
            
            # Davetiye kodunu kullanılmış olarak işaretle
            invitation.is_used = True
            invitation.used_by = user
            invitation.save()

            # Kullanıcının profilindeki davetiye kotasını güncelle
            user_profile = user.userprofile
            user_profile.invitation_quota += invitation.quota_granted
            user_profile.save()

            login(request, user)
            return redirect('user_homepage')
        else:
            # Form geçersizse hataları göster
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
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
    return redirect('user_profile', username=request.user.username)


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile_user.userprofile
    active_tab = request.GET.get('tab', 'sorular') 
    is_own_profile = request.user.is_authenticated and request.user == profile_user

    # Soru ve yanıt listeleri
    questions_list = Question.objects.filter(user=profile_user).order_by('-created_at')
    answers_list = Answer.objects.filter(user=profile_user).order_by('-created_at')

    # Sorular sayfalama
    question_page = request.GET.get('question_page', 1)
    question_paginator = Paginator(questions_list, 10)
    try:
        questions = question_paginator.page(question_page)
    except PageNotAnInteger:
        questions = question_paginator.page(1)
    except EmptyPage:
        questions = question_paginator.page(question_paginator.num_pages)

    # Yanıtlar sayfalama
    answer_page = request.GET.get('answer_page', 1)
    answer_paginator = Paginator(answers_list, 10)
    try:
        answers = answer_paginator.page(answer_page)
    except PageNotAnInteger:
        answers = answer_paginator.page(1)
    except EmptyPage:
        answers = answer_paginator.page(answer_paginator.num_pages)

    # Kelimeler sekmesi
    question_texts = questions_list.values_list('question_text', flat=True)
    answer_texts = answers_list.values_list('answer_text', flat=True)
    all_texts = (' '.join(question_texts) + ' ' + ' '.join(answer_texts)).lower()
    words = re.findall(r'\b\w+\b', all_texts)

    # Hariç tutulacak kelimeler virgüllerle ayrılmış tek bir parametreden alınır.
    exclude_words_str = request.GET.get('exclude_words', '')
    exclude_words_list = [w.strip() for w in exclude_words_str.split(',') if w.strip()]
    exclude_words_set = set(exclude_words_list)

    exclude_word = request.GET.get('exclude_word', '').strip().lower()
    if exclude_word:
        exclude_words_set.add(exclude_word)

    include_word = request.GET.get('include_word', '').strip().lower()
    if include_word and include_word in exclude_words_set:
        exclude_words_set.remove(include_word)

    # Güncellenen set'i tekrar stringe çevir
    exclude_words_list = list(exclude_words_set)
    exclude_words_list.sort()
    exclude_words_str = ', '.join(exclude_words_list)

    # Kelimeleri filtrele
    filtered_words = [word for word in words if word not in exclude_words_set]

    # Kelime sıklıkları
    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(20)

    # Kelime arama
    search_word = request.GET.get('search_word', '').strip().lower()
    search_word_count = None
    if search_word:
        search_word_count = word_counts.get(search_word, 0)

    # İstatistikler sekmesi
    total_upvotes = (Question.objects.filter(user=profile_user).aggregate(total=Coalesce(Sum('upvotes'), 0))['total'] +
                     Answer.objects.filter(user=profile_user).aggregate(total=Coalesce(Sum('upvotes'), 0))['total'])
    total_downvotes = (Question.objects.filter(user=profile_user).aggregate(total=Coalesce(Sum('downvotes'), 0))['total'] +
                       Answer.objects.filter(user=profile_user).aggregate(total=Coalesce(Sum('downvotes'), 0))['total'])

    content_type_question = ContentType.objects.get_for_model(Question)
    content_type_answer = ContentType.objects.get_for_model(Answer)
    total_saves_questions = SavedItem.objects.filter(content_type=content_type_question, object_id__in=questions_list).count()
    total_saves_answers = SavedItem.objects.filter(content_type=content_type_answer, object_id__in=answers_list).count()
    total_saves = total_saves_questions + total_saves_answers

    # En çok upvote alan girdi
    most_upvoted_question = questions_list.order_by('-upvotes').first()
    most_upvoted_answer = answers_list.order_by('-upvotes').first()
    most_upvoted_entry = max(
        (e for e in [most_upvoted_question, most_upvoted_answer] if e),
        key=lambda x: x.upvotes,
        default=None
    )

    # En çok downvote alan girdi
    most_downvoted_question = questions_list.order_by('-downvotes').first()
    most_downvoted_answer = answers_list.order_by('-downvotes').first()
    most_downvoted_entry = max(
        (e for e in [most_downvoted_question, most_downvoted_answer] if e),
        key=lambda x: x.downvotes,
        default=None
    )

    # En çok kaydedilen girdi
    most_saved_question = questions_list.annotate(save_count=Count('saveditem')).order_by('-save_count').first()
    most_saved_answer = answers_list.annotate(save_count=Count('saveditem')).order_by('-save_count').first()
    most_saved_entry = max(
        (e for e in [most_saved_question, most_saved_answer] if e),
        key=lambda x: x.save_count,
        default=None
    )

    follower_count = user_profile.followers.count()
    following_count = user_profile.following.count()

    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = request.user.userprofile.following.filter(user=profile_user).exists()

    try:
        pinned_entry = PinnedEntry.objects.get(user=profile_user)
    except PinnedEntry.DoesNotExist:
        pinned_entry = None

    if is_own_profile:
        invitations = Invitation.objects.filter(sender=request.user).order_by('-created_at')
        total_invitations = invitations.count()
        used_invitations = invitations.filter(is_used=True).count()
        remaining_invitations = user_profile.invitation_quota - total_invitations
    else:
        invitations = None
        total_invitations = 0
        used_invitations = 0
        remaining_invitations = 0

    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'questions': questions,
        'answers': answers,
        'top_words': top_words,
        'exclude_words': exclude_words_str,
        'search_word': search_word,
        'search_word_count': search_word_count,
        'total_upvotes': total_upvotes,
        'total_downvotes': total_downvotes,
        'total_saves': total_saves,
        'most_upvoted_entry': most_upvoted_entry,
        'most_downvoted_entry': most_downvoted_entry,
        'most_saved_entry': most_saved_entry,
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following,
        'is_own_profile': is_own_profile,
        'active_tab': active_tab,
        'exclude_words_list': exclude_words_list,
        'pinned_entry': pinned_entry,
        'invitations': invitations,
        'total_invitations': total_invitations,
        'used_invitations': used_invitations,
        'remaining_invitations': remaining_invitations,
    }

    return render(request, 'core/user_profile.html', context)

@login_required
def create_invitation(request):
    if request.method == 'POST':
        user_profile = request.user.userprofile
        total_invitations = Invitation.objects.filter(sender=request.user).count()
        remaining_invitations = user_profile.invitation_quota - total_invitations

        quota_granted = int(request.POST.get('quota_granted', 1))

        if quota_granted > remaining_invitations:
            messages.error(request, f"En fazla {remaining_invitations} adet davetiye kotası verebilirsiniz.")
        else:
            Invitation.objects.create(sender=request.user, quota_granted=quota_granted)
            # Kullanıcının davetiye kotasını azalt
            user_profile.invitation_quota -= quota_granted
            user_profile.save()
            messages.success(request, f"Davetiye oluşturuldu. Kullanıcıya {quota_granted} adet davetiye kotası verilecek.")

    # Yönlendirme yaparken 'tab' parametresini ekleyin
    return redirect(f'{reverse("user_profile", args=[request.user.username])}?tab=davetler')


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

    all_questions = get_today_questions(request)


    context = {
        'question': question,
        'answers': answers,
        'form': form,
        'user_has_saved_question': user_has_saved_question,
        'question_save_count': question_save_count,
        'saved_answer_ids': list(saved_answer_ids),
        'answer_save_dict': answer_save_dict,
        'all_questions': all_questions,
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
def user_list(request):
    users = User.objects.exclude(id=request.user.id)  # Exclude the current user
    User.objects.exclude(id=request.user.id).order_by('username')
    return render(request, 'core/user_list.html', {'users': users})

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
    all_questions = get_today_questions(request)
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
        'answer_form': answer_form,
        'all_questions': all_questions,
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
    all_questions = get_today_questions(request)
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
        'all_questions': all_questions,
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
        Q(questions__isnull=False) | Q(answers__isnull=False)
    ).distinct().count()

    # Toplam soru ve yanıt sayısı
    total_questions = Question.objects.count()
    total_answers = Answer.objects.count()

    # Toplam beğeni ve beğenmeme sayısı
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


def user_homepage(request):
    if not request.user.is_authenticated:
        return redirect('signup')
    
    today = timezone.now().date()

    # Tüm soruları al
    all_questions = get_today_questions(request)

    # Rastgele yanıtlar (Örnek)
    random_items = Answer.objects.all().order_by('?')[:10]


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
    focused_answer = get_object_or_404(Answer, id=answer_id, question=question)
    all_questions = get_today_questions(request)

    # Tüm yanıtlar
    all_answers = Answer.objects.filter(question=question).select_related('user')

    # Kullanıcının kaydettiği yanıtlar
    saved_answer_ids = SavedItem.objects.filter(
        user=request.user,
        content_type=ContentType.objects.get_for_model(Answer),
        object_id__in=all_answers.values_list('id', flat=True)
    ).values_list('object_id', flat=True)

    # Yanıtların kaydedilme sayısı
    content_type_answer = ContentType.objects.get_for_model(Answer)
    answer_save_counts = SavedItem.objects.filter(
        content_type=content_type_answer,
        object_id__in=all_answers.values_list('id', flat=True)
    ).values('object_id').annotate(count=Count('id'))
    answer_save_dict = {item['object_id']: item['count'] for item in answer_save_counts}

    # Kullanıcının oyları
    user_votes = Vote.objects.filter(
        user=request.user,
        content_type=content_type_answer,
        object_id__in=all_answers.values_list('id', flat=True)
    ).values('object_id', 'value')
    user_vote_dict = {vote['object_id']: vote['value'] for vote in user_votes}

    # Oy değerlerini her yanıta ekle
    for ans in all_answers:
        ans.user_vote_value = user_vote_dict.get(ans.id, 0)

    # Yanıt ekleme formu
    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            new_answer = form.save(commit=False)
            new_answer.question = question
            new_answer.user = request.user
            new_answer.save()
            return redirect('single_answer', question_id=question.id, answer_id=new_answer.id)
    else:
        form = AnswerForm()

    context = {
        'question': question,
        'focused_answer': focused_answer,
        'all_answers': all_answers,
        'saved_answer_ids': saved_answer_ids,
        'answer_save_dict': answer_save_dict,
        'form': form,  # Yanıt ekleme formu
        'all_questions': all_questions,
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
def pin_entry(request, answer_id):
    if request.method == 'POST':
        user = request.user
        # Mevcut sabitlenmiş girdiyi kaldır
        PinnedEntry.objects.filter(user=user).delete()
        # Yeni girdiyi sabitle
        answer = get_object_or_404(Answer, id=answer_id)
        PinnedEntry.objects.create(user=user, answer=answer)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def unpin_entry(request):
    if request.method == 'POST':
        user = request.user
        PinnedEntry.objects.filter(user=user).delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def update_profile_photo(request):
    profile_user = request.user
    user_profile = profile_user.userprofile

    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=user_profile)
        remove_photo = (request.POST.get('remove_photo') == 'true')

        if remove_photo:
            if user_profile.photo:
                user_profile.photo.delete(save=False)
            user_profile.photo = None
            user_profile.save()
            messages.success(request, 'Fotoğrafınız kaldırıldı.')
            return redirect('user_profile', username=profile_user.username)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profil fotoğrafınız güncellendi.')
            return redirect('user_profile', username=profile_user.username)
        else:
            # Form hatalıysa modal tekrar açılsın diye user_profile.html'i tekrar render ediyoruz.
            return render(request, 'core/user_profile.html', {
                'profile_user': profile_user,
                'user_profile': user_profile,
                'form': form,
                'is_own_profile': True,  # Kendi profilimiz olduğunu varsayıyoruz
            })
    else:
        # GET isteğinde direkt profiline yönlendir
        return redirect('user_profile', username=profile_user.username)


def get_top_words(user):
    answers = Answer.objects.filter(user=user)
    questions = Question.objects.filter(user=user)

    text = ' '.join([a.answer_text for a in answers] + [q.question_text for q in questions])
    words = re.findall(r'\w+', text.lower())
    word_counts = Counter(words)
    top_words = word_counts.most_common(10)

    return top_words


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def message_list(request):
    # Get all messages involving the user
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    )
    all_questions = get_today_questions(request)
    # Annotate each conversation with the latest message timestamp
    conversations = messages.values(
        'sender', 'recipient'
    ).annotate(
        last_message_time=Max('timestamp')
    ).order_by('-last_message_time')

    # Use a set to avoid duplicate user pairs
    conversation_users = []
    conversation_dict = {}

    for convo in conversations:
        # Determine the other user in the conversation
        if convo['sender'] == request.user.id:
            other_user_id = convo['recipient']
        else:
            other_user_id = convo['sender']

        if other_user_id not in conversation_users:
            other_user = User.objects.get(id=other_user_id)
            # Fetch messages with this user
            messages_with_user = messages.filter(
                Q(sender=other_user, recipient=request.user) |
                Q(sender=request.user, recipient=other_user)
            ).order_by('-timestamp')

            # Count unread messages from other_user to request.user
            unread_count = messages_with_user.filter(
                sender=other_user,
                recipient=request.user,
                is_read=False
            ).count()

            conversation_dict[other_user] = {
                'messages': messages_with_user,
                'unread_count': unread_count,
                'all_questions': all_questions,
            }

            conversation_users.append(other_user_id)


    context = {
        'conversations': conversation_dict,
        'all_questions': all_questions,
    }
    return render(request, 'core/message_list.html', context)


@login_required
def message_detail(request, username):
    other_user = get_object_or_404(User, username=username)
    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)

    # Mesajları doğru şekilde sıralayın: en eski önce, en yeni sonra
    messages = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')  # 'timestamp' alanına göre artan sırada
    
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            Message.objects.create(
                sender=request.user,
                recipient=other_user,
                body=body,
                timestamp=timezone.now(),
                is_read=False
            )
            # Diğer kullanıcının mesajlarını okunmuş olarak işaretlemek isteğe bağlıdır
            Message.objects.filter(sender=other_user, recipient=request.user).update(is_read=True)
            return redirect('message_detail', username=username)
    all_questions = get_today_questions(request)

    context = {
        'other_user': other_user,
        'messages': messages,
        'all_questions': all_questions,
    }
    return render(request, 'core/message_detail.html', context)

@login_required
def send_message_from_answer(request, answer_id):
    from .models import Answer
    answer = get_object_or_404(Answer, id=answer_id)
    recipient = answer.user

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            return redirect('message_detail', username=recipient.username)
    else:
        form = MessageForm(initial={'recipient': recipient})

    context = {
        'form': form,
        'recipient': recipient,
        'answer': answer,
    }
    return render(request, 'core/send_message_from_answer.html', context)

@login_required
def check_new_messages(request):
    # Kullanıcının okunmamış mesajlarını say
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def send_message_from_user(request, user_id):
    recipient = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            return redirect('message_detail', username=recipient.username)
    else:
        form = MessageForm()

    context = {
        'form': form,
        'recipient': recipient,
    }
    return render(request, 'core/send_message_from_answer.html', context)


def get_today_questions(request, per_page=25):
    """Bugün oluşturulan veya bugün yanıt alan soruları döndürür (sayfalandırılmış), 
    en son yanıtlananlar en üste gelecek şekilde sıralar."""

    today = timezone.now().date()
    queryset = Question.objects.annotate(
        answers_count=Count('answers', distinct=True),  # distinct=True eklendi
        latest_answer_date=Max('answers__created_at')
    ).filter(
        Q(created_at__date=today) | Q(answers__created_at__date=today)
    ).distinct()

    # sort_date için Coalesce kullanımı
    queryset = queryset.annotate(
        sort_date=Coalesce('latest_answer_date', 'created_at')
    ).order_by(F('sort_date').desc())

    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, per_page)
    try:
        all_questions = paginator.page(page)
    except PageNotAnInteger:
        all_questions = paginator.page(1)
    except EmptyPage:
        all_questions = paginator.page(paginator.num_pages)

    return all_questions



def custom_404_view(request, exception):
    # 404 sayfası için özel view
    # Status kodunu 404 olarak ayarlamayı unutmayın.
    response = render(request, 'core/404.html')
    response.status_code = 404
    return response

def get_random_sentence(request):
    # Veritabanından rastgele bir cümle çek
    sentences_count = RandomSentence.objects.count()
    if sentences_count == 0:
        # Hiç cümle yoksa sabit bir mesaj dön
        return JsonResponse({'sentence': 'Henüz eklenmiş bir cümle yok.'})
    random_index = random.randint(0, sentences_count - 1)
    sentence = RandomSentence.objects.all()[random_index].sentence
    return JsonResponse({'sentence': sentence})

@require_POST
def add_random_sentence(request):
    form = RandomSentenceForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success', 'message': 'Cümle eklendi!'})
    else:
        # Form geçersiz ise hata mesajını döndür
        errors = form.errors.get_json_data()
        return JsonResponse({'status': 'error', 'errors': errors})
    

#POLLS
@login_required
def polls_home(request):
    # Aktif anketler (end_date > şu an)
    active_polls = Poll.objects.filter(end_date__gt=timezone.now()).order_by('-created_at')
    # Süresi geçmiş anketler (end_date <= şu an)
    expired_polls = Poll.objects.filter(end_date__lte=timezone.now()).order_by('-created_at')

    # Süresi geçmiş anketler için yüzdeleri hesaplayalım
    expired_polls_data = []
    for poll in expired_polls:
        options_data = []
        total_votes = sum([opt.votes.count() for opt in poll.options.all()])
        for opt in poll.options.all():
            if total_votes > 0:
                percentage = (opt.votes.count() / total_votes) * 100
            else:
                percentage = 0
            options_data.append({
                'text': opt.option_text,
                'percentage': f"{percentage:.2f}"
            })
        expired_polls_data.append({
            'poll': poll,
            'options_data': options_data
        })

    form = PollForm()
    return render(request, 'core/polls.html', {
        'active_polls': active_polls,
        'expired_polls_data': expired_polls_data,
        'form': form
    })

@login_required
def create_poll(request):
    if request.method == 'POST':
        form = PollForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question_text']
            end_date = form.cleaned_data['end_date']
            is_anonymous = form.cleaned_data['is_anonymous']
            options = form.cleaned_data['options']

            poll = Poll.objects.create(
                question_text=question_text,
                created_by=request.user,
                end_date=end_date,
                is_anonymous=is_anonymous
            )
            for opt_text in options:
                PollOption.objects.create(poll=poll, option_text=opt_text)
            
            messages.success(request, 'Anket başarıyla oluşturuldu.')
            return redirect('polls_home')
        else:
            # Form geçersizse hata mesajlarını göster
            return render(request, 'core/create_poll.html', {'form': form})
    else:
        form = PollForm()
        return render(request, 'core/create_poll.html', {'form': form})

@login_required
def vote_poll(request, poll_id, option_id):
    poll = get_object_or_404(Poll, id=poll_id)
    option = get_object_or_404(PollOption, id=option_id, poll=poll)

    # Kullanıcı daha önce bu ankette oy vermiş mi?
    # Aynı ankete birden fazla oy vermesin.
    if PollVote.objects.filter(user=request.user, option__poll=poll).exists():
        messages.error(request, 'Bu ankete daha önce oy verdiniz.')
        return redirect('polls_home')

    if poll.is_active():
        PollVote.objects.create(user=request.user, option=option)
        messages.success(request, 'Oyunuz kaydedildi.')
    else:
        messages.error(request, 'Bu anket süresi dolmuş.')
    return redirect('polls_home')

@login_required
def poll_question_redirect(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if poll.related_question:
        # Soru mevcutsa direkt oraya git
        return redirect('question_detail', question_id=poll.related_question.id)
    else:
        # Yeni başlık oluştur
        q = Question.objects.create(
            question_text=f"anket:{poll.question_text}",
            user=request.user
        )
        q.users.add(request.user)
        poll.related_question = q
        poll.save()
        return redirect('question_detail', question_id=q.id)