from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('send-invitation/', views.send_invitation, name='send_invitation'),
    path('profile/', views.profile, name='profile'),
    path('add-question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('question/<int:question_id>/add-answer/', views.add_answer, name='add_answer'),
    path('messages/sent/', views.sent_messages, name='sent_messages'),
    path('messages/<int:message_id>/', views.view_message, name='view_message'),
    path('ajax/get_unread_message_count/', views.get_unread_message_count, name='get_unread_message_count'),
    path('messages/get_conversation/<str:username>/', views.get_conversation, name='get_conversation'),
    path('messages/send_ajax/', views.send_message_ajax, name='send_message_ajax'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('users/', views.user_list, name='user_list'),
    path('conversations/', views.conversations, name='conversations'),
    path('messages/check_new_messages/', views.check_new_messages, name='check_new_messages'),
    path('messages/unread_count/', views.get_unread_message_count, name='get_unread_message_count'),
    path('user/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('user/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('search_suggestions/', views.search_suggestions, name='search_suggestions'),
    path('search/', views.search, name='search'),
    path('add_question_from_search/', views.add_question_from_search, name='add_question_from_search'),
    path('users/get_user_id/<str:username>/', views.get_user_id, name='get_user_id'),
]

