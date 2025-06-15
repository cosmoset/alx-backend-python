from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent_message = models.ForeignKey(
        "self", null=True, blank=True, related_name="replies", on_delete=models.SET_NULL
    )

    # New field for threading
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    edited_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="edited_messages",
    )

    # Default manager
    objects = models.Manager()

    # Custom manager for unread messages
    unread = UnreadMessagesManager()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["sender", "receiver"]),
            models.Index(fields=["parent_message"]),
            models.Index(fields=["receiver", "is_read"]),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.content[:30]}"

    def get_thread(self):
        """Recursively get all messages in this thread"""
        messages = []
        self._get_thread_recursive(messages)
        return messages

    def _get_thread_recursive(self, messages):
        """Helper method for recursive thread collection"""
        messages.append(self)
        for reply in self.replies.all():
            reply._get_thread_recursive(messages)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"

    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="notifications"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user} about message {self.message.id}"


class MessageHistory(models.Model):
    message = models.ForeignKey(
        Message, related_name="history", on_delete=models.CASCADE
    )
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History for Msg ID {self.message.id} at {self.edited_at}"
