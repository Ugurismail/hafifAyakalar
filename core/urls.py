from django.urls import path
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
    path('profile/pin_entry/<str:entry_type>/<int:entry_id>/', views.pin_entry, name='pin_entry'),
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
    
    #mesajlar
    path('messages/send_ajax/', views.send_message_ajax, name='send_message_ajax'),
    path('messages/mark_as_read/', views.mark_messages_as_read, name='mark_messages_as_read'),
    path('messages/check_new_messages/', views.check_new_messages, name='check_new_messages'),
    path('messages/unread_count/', views.get_unread_message_count, name='get_unread_message_count'),
    path('messages/<str:username>/', views.get_conversation, name='get_conversation'),
    path('messages/', views.conversations, name='conversations'),

    # Arama
    path('search/', views.search, name='search'),
    path('search_suggestions/', views.search_suggestions, name='search_suggestions'),
    path('reference-search/', views.reference_search, name='reference_search'),
    path('user-search/', views.user_search, name='user_search'),

    #kullanıcı ayarları
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
    path('send-invitation/', views.send_invitation, name='send_invitation'),
    

]
