from django.contrib import admin
from .models import Message, Notification, MessageHistory
from django.utils.html import format_html


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender_info",
        "receiver_info",
        "content_preview",
        "timestamp",
        "is_read",
    )
    list_filter = ("is_read", "timestamp", "sender", "receiver")
    search_fields = ("content", "sender__username", "receiver__username")
    date_hierarchy = "timestamp"
    actions = ["mark_as_read", "mark_as_unread"]
    readonly_fields = ("timestamp",)

    def sender_info(self, obj):
        return format_html(
            "<strong>{}</strong><br><small>{}</small>",
            obj.sender.username,
            obj.sender.email,
        )

    sender_info.short_description = "Sender"

    def receiver_info(self, obj):
        return format_html(
            "<strong>{}</strong><br><small>{}</small>",
            obj.receiver.username,
            obj.receiver.email,
        )

    receiver_info.short_description = "Receiver"

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content Preview"

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} messages marked as read")

    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} messages marked as unread")

    mark_as_unread.short_description = "Mark selected messages as unread"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_info", "message_link", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "message__content")
    date_hierarchy = "created_at"
    actions = ["mark_as_read", "mark_as_unread"]
    raw_id_fields = ("message",)

    def user_info(self, obj):
        return format_html(
            "<strong>{}</strong><br><small>{}</small>",
            obj.user.username,
            obj.user.email,
        )

    user_info.short_description = "User"

    def message_link(self, obj):
        return format_html(
            '<a href="/admin/messaging/message/{}/change/">{}</a>',
            obj.message.id,
            (
                obj.message.content[:50] + "..."
                if len(obj.message.content) > 50
                else obj.message.content
            ),
        )

    message_link.short_description = "Message"
    message_link.admin_order_field = "message__content"

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notifications marked as read")

    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notifications marked as unread")

    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "message_link", "original_content_preview", "modified_at")
    search_fields = ("original_content", "message__content")
    date_hierarchy = "modified_at"
    raw_id_fields = ("message",)

    def message_link(self, obj):
        return format_html(
            '<a href="/admin/messaging/message/{}/change/">{}</a>',
            obj.message.id,
            f"Message #{obj.message.id}",
        )

    message_link.short_description = "Message"

    def original_content_preview(self, obj):
        return (
            obj.original_content[:100] + "..."
            if len(obj.original_content) > 100
            else obj.original_content
        )

    original_content_preview.short_description = "Original Content"
