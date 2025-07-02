from django.urls import path
from . import views

urlpatterns = [
    # Home and Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # User Management
    path('profile/', views.user_profile, name='user_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    
    # Message Management
    path('send/', views.send_message, name='send_message'),
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent_messages, name='sent_messages'),
    path('unread/', views.unread_inbox, name='unread_inbox'),
    path('unread-threads/', views.unread_threads, name='unread_threads'),
    
    # Threading and Conversation Views
    path('thread/<int:message_id>/', views.view_thread, name='view_thread'),
    path('threaded/', views.threaded_conversations, name='threaded_conversations'),
    path('thread-recursive/<int:message_id>/', views.display_thread_recursive, name='display_thread_recursive'),
    path('optimized-list/', views.optimized_message_list, name='optimized_message_list'),
    
    # Message Actions
    path('edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('history/<int:message_id>/', views.message_history, name='message_history'),
    path('mark-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('mark-thread-read/<int:message_id>/', views.mark_thread_read, name='mark_thread_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('bulk-mark-read/', views.bulk_mark_read, name='bulk_mark_read'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Search and Analytics
    path('search/', views.search_messages, name='search_messages'),
    path('stats/', views.message_stats, name='message_stats'),
    path('analytics/', views.message_analytics, name='message_analytics'),
    path('export/', views.export_messages, name='export_messages'),
    
    # API Endpoints (AJAX)
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/recent-messages/', views.api_recent_messages, name='api_recent_messages'),
    path('api/user-suggestions/', views.get_user_suggestions, name='api_user_suggestions'),
]