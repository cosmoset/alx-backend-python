from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import uuid


class User(AbstractUser):
    """
    Extended User model with additional fields for messaging functionality.
    Extends Django's AbstractUser to add custom fields.
    """
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Explicitly define password field
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'chats_user'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Conversation(models.Model):
    """
    Model to track conversations between users.
    A conversation can have multiple participants.
    """
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(
        'User',
        related_name='conversations',
        help_text="Users participating in this conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chats_conversation'
        ordering = ['-updated_at']

    def __str__(self):
        participant_names = ", ".join([str(user) for user in self.participants.all()[:3]])
        if self.participants.count() > 3:
            participant_names += f" and {self.participants.count() - 3} others"
        return f"Conversation: {participant_names}"

    def get_participant_count(self):
        """Return the number of participants in the conversation."""
        return self.participants.count()


class Message(models.Model):
    """
    Model representing individual messages in conversations.
    Each message belongs to a conversation and has a sender.
    """
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="User who sent this message"
    )
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Conversation this message belongs to"
    )
    message_body = models.TextField(help_text="Content of the message")
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chats_message'
        ordering = ['sent_at']

    def __str__(self):
        return f"Message from {self.sender.first_name} at {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    def get_sender_name(self):
        """Return the full name of the message sender."""
        return f"{self.sender.first_name} {self.sender.last_name}"