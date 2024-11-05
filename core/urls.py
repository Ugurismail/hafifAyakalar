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
    path('profile/', views.profile, name='profile'),  # Kullanıcının kendi profil sayfası
    path('profile/<str:username>/', views.user_profile, name='user_profile'),  # Diğer kullanıcıların profilleri
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('settings/', views.user_settings, name='user_settings'),

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
    path('delete-answer/<int:answer_id>/', views.delete_answer, name='delete_answer'),

    # Mesajlaşma
    path('messages/sent/', views.sent_messages, name='sent_messages'),
    path('messages/<int:message_id>/', views.view_message, name='view_message'),
    path('messages/get_conversation/<str:username>/', views.get_conversation, name='get_conversation'),
    path('messages/send_ajax/', views.send_message_ajax, name='send_message_ajax'),
    path('messages/mark_as_read/', views.mark_messages_as_read, name='mark_messages_as_read'),
    path('messages/check_new_messages/', views.check_new_messages, name='check_new_messages'),
    path('messages/unread_count/', views.get_unread_message_count, name='get_unread_message_count'),
    path('conversations/', views.conversations, name='conversations'),
    path('send-invitation/', views.send_invitation, name='send_invitation'),

    # Arama
    path('search/', views.search, name='search'),
    path('search_suggestions/', views.search_suggestions, name='search_suggestions'),
    path('reference-search/', views.reference_search, name='reference_search'),
    path('user-search/', views.user_search, name='user_search'),

    # Diğer İşlemler
    path('about/', views.about, name='about'),
    path('statistics/', views.site_statistics, name='site_statistics'),
    path('map/', views.question_map, name='question_map'),
    path('map-data/', views.map_data, name='map_data'),
    path('add-starting-question/', views.add_starting_question, name='add_starting_question'),
    path('add_question_from_search/', views.add_question_from_search, name='add_question_from_search'),
    path('bkz/<path:query>/', views.bkz_view, name='bkz'),
    path('users/', views.user_list, name='user_list'),

    # AJAX İşlemleri
    path('ajax/get_unread_message_count/', views.get_unread_message_count, name='get_unread_message_count'),
    path('users/get_user_id/<str:username>/', views.get_user_id, name='get_user_id'),
    path('vote/', views.vote, name='vote'),
    path('save-item/', views.save_item, name='save_item'),

]




    # path('', views.user_homepage, name='user_homepage'),
    # path('signup/', views.signup, name='signup'),
    # path('login/', views.user_login, name='login'),
    # path('logout/', views.user_logout, name='logout'),
    # path('send-invitation/', views.send_invitation, name='send_invitation'),
    # path('profile/', views.profile, name='profile'),
    # path('add-question/', views.add_question, name='add_question'),
    # path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    # path('question/<int:question_id>/add-answer/', views.add_answer, name='add_answer'),
    # path('messages/sent/', views.sent_messages, name='sent_messages'),
    # path('messages/<int:message_id>/', views.view_message, name='view_message'),
    # path('ajax/get_unread_message_count/', views.get_unread_message_count, name='get_unread_message_count'),
    # path('messages/get_conversation/<str:username>/', views.get_conversation, name='get_conversation'),
    # path('messages/send_ajax/', views.send_message_ajax, name='send_message_ajax'),
    # path('user/<str:username>/', views.user_profile, name='user_profile'),
    # path('users/', views.user_list, name='user_list'),
    # path('conversations/', views.conversations, name='conversations'),
    # path('messages/check_new_messages/', views.check_new_messages, name='check_new_messages'),
    # path('messages/unread_count/', views.get_unread_message_count, name='get_unread_message_count'),
    # path('user/<str:username>/follow/', views.follow_user, name='follow_user'),
    # path('user/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    # path('search_suggestions/', views.search_suggestions, name='search_suggestions'),
    # path('search/', views.search, name='search'),
    # path('add_question_from_search/', views.add_question_from_search, name='add_question_from_search'),
    # path('users/get_user_id/<str:username>/', views.get_user_id, name='get_user_id'),
    # path('question/<int:question_id>/add-subquestion/', views.add_subquestion, name='add_subquestion'),
    # path('about/', views.about, name='about'),
    # path('ayarlar/', views.user_settings, name='user_settings'),
    # path('statistics/', views.site_statistics, name='site_statistics'),
    # path('map/', views.question_map, name='question_map'),
    # path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),
    # path('answer/<int:answer_id>/delete/', views.delete_answer, name='delete_answer'),
    # path('add-starting-question/', views.add_starting_question, name='add_starting_question'),
    # path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    # path('question/<int:question_id>/answer/<int:answer_id>/', views.single_answer, name='single_answer'),
    # path('map-data/', views.map_data, name='map_data'),
    # path('user-search/', views.user_search, name='user_search'),
    # path('messages/mark_as_read/', views.mark_messages_as_read, name='mark_messages_as_read'),
    # path('bkz/<str:query>/', views.bkz_view, name='bkz'),
    # path('add_question_from_search/', views.add_question_from_search, name='add_question_from_search'),
    # path('reference-search/', views.reference_search, name='reference_search'),
    # path('profile/<str:username>/', views.user_profile, name='user_profile'),





# urlpatterns = [
#     path('', views.user_homepage, name='user_homepage'),
#     path('add-starting-question/', views.add_starting_question, name='add_starting_question'),
#     path('signup/', views.signup, name='signup'),
#     path('login/', views.user_login, name='login'),
#     path('logout/', views.user_logout, name='logout'),
#     path('profile/', views.profile, name='profile'),
#     path('profile/<str:username>/', views.profile, name='profile'),
#     path('add-question/', views.add_question, name='add_question'),
#     path('question/<int:question_id>/', views.question_detail, name='question_detail'),
#     path('question/<int:question_id>/add-subquestion/', views.add_subquestion, name='add_subquestion'),
#     path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),
#     path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
#     path('map/', views.question_map, name='question_map'),
#     path('search/', views.search, name='search'),
#     path('user-search/', views.user_search, name='user_search'),
#     path('map-data/', views.map_data, name='map_data'),
#     path('vote/', views.vote, name='vote'),
#     path('save-item/', views.save_item, name='save_item'),
#     path('delete-saved-item/<int:item_id>/', views.delete_saved_item, name='delete_saved_item'),
#     path('user/<str:username>/', views.user_profile, name='user_profile'),
#     path('profile/<str:username>/', views.profile, name='profile_with_username'),
#     path('about/', views.about, name='about'),
#     path('statistics/', views.site_statistics, name='site_statistics'),
#     path('answer/<int:answer_id>/delete/', views.delete_answer, name='delete_answer'),
#     path('profile/<str:username>/', views.user_profile, name='profile'),
#     path('messages/', views.inbox, name='inbox'),
#     path('messages/sent/', views.sent_messages, name='sent_messages'),
#     path('messages/compose/<str:username>/', views.compose_message, name='compose_message'),
#     path('messages/compose/', views.compose_message, name='compose_message_no_recipient'),
#     path('messages/<int:message_id>/', views.view_message, name='view_message'),
#     path('ajax/get_unread_message_count/', views.get_unread_message_count, name='get_unread_message_count'),
#     path('send-invitation/', views.send_invitation, name='send_invitation'),
#     path('grant-invitation-quota/', views.grant_invitation_quota, name='grant_invitation_quota'),
#     path('question/<int:question_id>/answer/<int:answer_id>/', views.single_answer, name='single_answer'),
#     path('ayarlar/', views.user_settings, name='user_settings'),
# ]