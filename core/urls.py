from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Ana Sayfa
    path('', views.user_homepage, name='user_homepage'),

    # Kullanıcı Kayıt ve Giriş
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Kullanıcı Profili
    path('profile/update_photo/', views.update_profile_photo, name='update_profile_photo'),
    path('pin_entry/answer/<int:answer_id>/', views.pin_entry, name='pin_entry'),
    path('unpin_entry/', views.unpin_entry, name='unpin_entry'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),

    # Soru İşlemleri
    path('add-question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('question/<int:question_id>/add-answer/', views.add_answer, name='add_answer'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('question/<int:question_id>/add-subquestion/', views.add_subquestion, name='add_subquestion'),
    path('question/<int:question_id>/answer/<int:answer_id>/', views.single_answer, name='single_answer'),

    # Yanıt İşlemleri
    path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),
    path('answer/<int:answer_id>/delete/', views.delete_answer, name='delete_answer'),

    # Mesajlaşma URL'leri
    path('messages/', views.message_list, name='message_list'),
    path('messages/<str:username>/', views.message_detail, name='message_detail'),
    path('send_message/answer/<int:answer_id>/', views.send_message_from_answer, name='send_message_from_answer'),
    path('check_new_messages/', views.check_new_messages, name='check_new_messages'),
    path('send_message/user/<int:user_id>/', views.send_message_from_user, name='send_message_from_user'),

    # Arama
    path('search/', views.search, name='search'),
    path('search_suggestions/', views.search_suggestions, name='search_suggestions'),
    path('reference-search/', views.reference_search, name='reference_search'),
    path('user-search/', views.user_search, name='user_search'),

    # Kullanıcı Ayarları
    path('settings/', views.user_settings, name='user_settings'),

    # Diğer İşlemler
    path('about/', views.about, name='about'),
    path('statistics/', views.site_statistics, name='site_statistics'),
    path('map/', views.question_map, name='question_map'),
    path('map-data/', views.map_data, name='map_data'),
    path('add-starting-question/', views.add_starting_question, name='add_starting_question'),
    path('add_question_from_search/', views.add_question_from_search, name='add_question_from_search'),
    path('bkz/<path:query>/', views.bkz_view, name='bkz'),

    # AJAX İşlemleri
    path('vote/', views.vote, name='vote'),
    path('save-item/', views.save_item, name='save_item'),
    path('users/', views.user_list, name='user_list'),
    path('create_invitation/', views.create_invitation, name='create_invitation'),
    path('send-invitation/', views.send_invitation, name='send_invitation'),

    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='core/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='core/password_change_done.html'), name='password_change_done'),

    path('random_sentence/', views.get_random_sentence, name='get_random_sentence'),
    path('add_random_sentence/', views.add_random_sentence, name='add_random_sentence'),
    path('ignore_random_sentence/', views.ignore_random_sentence, name='ignore_random_sentence'),

    # ANKETLER/POLL URL'LERİ (tamamı "polls/" prefixli)
    path('polls/', views.polls_home, name='polls_home'),
    path('polls/create/', views.create_poll, name='create_poll'),
    path('polls/<int:poll_id>/vote/<int:option_id>/', views.vote_poll, name='vote_poll'),
    path('polls/<int:poll_id>/question/', views.poll_question_redirect, name='poll_question_redirect'),
    path('polls/<int:poll_id>/popover/', views.poll_popover_content, name='poll_popover'),
    path('polls/<int:poll_id>/vote-ajax/', views.vote_poll_ajax, name='vote_poll_ajax'),
    path('polls/<int:poll_id>/', views.poll_detail, name='poll_detail'),

    # Tanımlar ve referanslar (diğer özel işlemler)
    path('create-definition/<int:question_id>/', views.create_definition, name='create_definition'),
    path('get-user-definitions/', views.get_user_definitions, name='get_user_definitions'),
    path('definition/<int:definition_id>/edit/', views.edit_definition, name='edit_definition'),
    path('definition/<int:definition_id>/delete/', views.delete_definition, name='delete_definition'),
    path('get-all-definitions/', views.get_all_definitions, name='get_all_definitions'),
    path('create-reference/', views.create_reference, name='create_reference'),
    path('get-references/', views.get_references, name='get_references'),
    path('reference/<int:reference_id>/edit/', views.edit_reference, name='edit_reference'),
    path('reference/<int:reference_id>/delete/', views.delete_reference, name='delete_reference'),
    # path('profile/<str:username>/download_entries/', views.download_entries, name='download_entries'),
    path('profile/<str:username>/download_entries_json/', views.download_entries_json, name='download_entries_json'),
    path('profile/<str:username>/download_entries_xlsx/', views.download_entries_xlsx, name='download_entries_xlsx'),
    path('question/<int:question_id>/filter_answers/', views.filter_answers, name='filter_answers'),
    path('profile/<str:username>/download_entries_docx/', views.download_entries_docx, name='download_entries_docx'),

    # Aramalar
    path('get-user-questions/', views.get_user_questions, name='get_user_questions'),
    path('get-user-answers/', views.get_user_answers, name='get_user_answers'),
    path('get-saved-items/', views.get_saved_items, name='get_saved_items'),
]

handler404 = 'core.views.custom_404_view'
