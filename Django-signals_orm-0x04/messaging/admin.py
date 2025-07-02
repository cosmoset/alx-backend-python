from django.contrib import admin
from .models import Message, Notification, MessageHistory


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'content_preview', 'timestamp', 'is_read', 'edited', 'last_edited']
    list_filter = ['timestamp', 'is_read', 'edited', 'sender', 'receiver']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['timestamp', 'edited', 'last_edited']
    list_per_page = 25
    
    fieldsets = (
        ('Message Info', {
            'fields': ('sender', 'receiver', 'content')
        }),
        ('Status', {
            'fields': ('is_read', 'edited', 'timestamp', 'last_edited')
        }),
    )

    def content_preview(self, obj):
        """Show a preview of the message content"""
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return f"{preview} {'(Edited)' if obj.edited else ''}"
    content_preview.short_description = 'Content Preview'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('sender', 'receiver')


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ['message_info', 'edited_by', 'edited_at', 'old_content_preview']
    list_filter = ['edited_at', 'edited_by']
    search_fields = ['message__content', 'old_content', 'edited_by__username']
    readonly_fields = ['edited_at']
    list_per_page = 25
    
    fieldsets = (
        ('Edit Info', {
            'fields': ('message', 'edited_by', 'edited_at')
        }),
        ('Content', {
            'fields': ('old_content', 'edit_reason')
        }),
    )

    def message_info(self, obj):
        """Show message info"""
        return f"Message {obj.message.id} ({obj.message.sender.username} → {obj.message.receiver.username})"
    message_info.short_description = 'Message'

    def old_content_preview(self, obj):
        """Show preview of old content"""
        return obj.old_content[:50] + '...' if len(obj.old_content) > 50 else obj.old_content
    old_content_preview.short_description = 'Old Content Preview'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('message', 'edited_by', 'message__sender', 'message__receiver')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'content']
    readonly_fields = ['created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('user', 'title', 'content', 'notification_type')
        }),
        ('Related', {
            'fields': ('message',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'message')

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'