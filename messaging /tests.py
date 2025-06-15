from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory
from django.db.models.signals import post_save
from django.dispatch import receiver


class MessagingSignalTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username="alice", password="pass123", email="alice@example.com"
        )
        self.receiver = User.objects.create_user(
            username="bob", password="pass123", email="bob@example.com"
        )

    def test_notification_created_on_message(self):
        """Test that a notification is automatically created when a message is sent"""
        message = Message.objects.create(
            sender=self.sender, receiver=self.receiver, content="Hello Bob!"
        )

        # Verify notification was created
        self.assertEqual(Notification.objects.count(), 1)

        notification = Notification.objects.first()
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.user.username, "bob")
        self.assertEqual(notification.message, message)

    def test_no_notification_on_message_update(self):
        """Test that notifications aren't created when updating existing messages"""
        message = Message.objects.create(
            sender=self.sender, receiver=self.receiver, content="Initial message"
        )

        # Update the message
        message.content = "Updated content"
        message.save()

        # Should still only have one notification
        self.assertEqual(Notification.objects.count(), 1)

    def test_message_history_creation(self):
        """Test message history is created when message is updated"""
        message = Message.objects.create(
            sender=self.sender, receiver=self.receiver, content="Original content"
        )

        # Update the message
        message.content = "Modified content"
        message.save()

        # Verify history was created
        self.assertEqual(MessageHistory.objects.count(), 1)
        history = MessageHistory.objects.first()
        self.assertEqual(history.original_content, "Original content")
        self.assertEqual(history.message, message)

    def test_message_str_representation(self):
        message = Message.objects.create(
            sender=self.sender, receiver=self.receiver, content="Test message"
        )
        self.assertIn("alice", str(message))
        self.assertIn("bob", str(message))
        self.assertIn("Test message", str(message))
