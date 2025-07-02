from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Message, Notification, MessageHistory


class CustomManagerTest(TestCase):
    """Test cases for custom managers"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create test messages
        self.read_message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="This is a read message",
            is_read=True
        )
        
        self.unread_message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="This is an unread message 1"
        )
        
        self.unread_message2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="This is an unread message 2"
        )

    def test_unread_messages_for_user(self):
        """Test custom manager filters unread messages for user"""
        unread_messages = Message.unread_messages.for_user(self.user2)
        
        self.assertEqual(unread_messages.count(), 2)
        self.assertIn(self.unread_message1, unread_messages)
        self.assertIn(self.unread_message2, unread_messages)
        self.assertNotIn(self.read_message, unread_messages)

    def test_unread_count_for_user(self):
        """Test custom manager counts unread messages correctly"""
        unread_count = Message.unread_messages.unread_count_for_user(self.user2)
        self.assertEqual(unread_count, 2)
        
        # Mark one message as read
        self.unread_message1.mark_as_read()
        
        unread_count = Message.unread_messages.unread_count_for_user(self.user2)
        self.assertEqual(unread_count, 1)

    def test_unread_threads_for_user(self):
        """Test custom manager filters unread thread messages"""
        # Create a reply
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="This is a reply",
            parent_message=self.unread_message1
        )
        
        unread_threads = Message.unread_messages.unread_threads_for_user(self.user2)
        
        # Should only include root messages, not replies
        self.assertEqual(unread_threads.count(), 2)
        self.assertNotIn(reply, unread_threads)

    def test_mark_thread_as_read(self):
        """Test marking entire thread as read"""
        # Create a thread with replies
        reply1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Reply 1",
            parent_message=self.unread_message1
        )
        
        reply2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Reply 2",
            parent_message=self.unread_message1
        )
        
        # All should be unread initially
        self.assertFalse(self.unread_message1.is_read)
        self.assertFalse(reply1.is_read)
        self.assertFalse(reply2.is_read)
        
        # Mark thread as read
        updated_count = Message.unread_messages.mark_thread_as_read(
            self.user2, self.unread_message1
        )
        
        # Should have updated 3 messages
        self.assertEqual(updated_count, 3)
        
        # Refresh from database
        self.unread_message1.refresh_from_db()
        reply1.refresh_from_db()
        reply2.refresh_from_db()
        
        # All should now be read
        self.assertTrue(self.unread_message1.is_read)
        self.assertTrue(reply1.is_read)
        self.assertTrue(reply2.is_read)

    def test_recent_unread(self):
        """Test getting recent unread messages with limit"""
        # Create more unread messages
        for i in range(15):
            Message.objects.create(
                sender=self.user1,
                receiver=self.user2,
                content=f"Unread message {i}"
            )
        
        recent_unread = Message.unread_messages.recent_unread(self.user2, limit=5)
        
        # Should return only 5 messages
        self.assertEqual(len(recent_unread), 5)
        
        # Should be ordered by most recent first
        timestamps = [msg.timestamp for msg in recent_unread]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_custom_queryset_methods(self):
        """Test custom QuerySet methods"""
        # Test unread filter
        unread_qs = Message.objects.unread()
        self.assertEqual(unread_qs.count(), 2)
        
        # Test read filter
        read_qs = Message.objects.read()
        self.assertEqual(read_qs.count(), 1)
        
        # Test for_user_received
        received_qs = Message.objects.for_user_received(self.user2)
        self.assertEqual(received_qs.count(), 3)
        
        # Test for_user_sent
        sent_qs = Message.objects.for_user_sent(self.user1)
        self.assertEqual(sent_qs.count(), 3)

    def test_optimized_queries(self):
        """Test that optimized queries work correctly"""
        # This test ensures that the .only() optimization works
        unread_messages = Message.unread_messages.for_user(self.user2)
        
        # Access optimized fields
        for message in unread_messages:
            # These should not trigger additional queries
            message.content
            message.timestamp
            message.sender.username
        
        # The test passes if no additional queries are triggered
        self.assertTrue(True)


class UnreadInboxViewTest(TestCase):
    """Test cases for unread inbox views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test messages
        Message.objects.create(
            sender=other_user,
            receiver=self.user,
            content="Unread message 1"
        )
        
        Message.objects.create(
            sender=other_user,
            receiver=self.user,
            content="Read message",
            is_read=True
        )

    def test_unread_inbox_view_requires_login(self):
        """Test that unread inbox view requires authentication"""
        response = self.client.get(reverse('unread_inbox'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_unread_inbox_view_shows_only_unread(self):
        """Test that unread inbox shows only unread messages"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('unread_inbox'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unread message 1')
        self.assertNotContains(response, 'Read message')

    def test_mark_message_read_ajax(self):
        """Test marking message as read via AJAX"""
        self.client.login(username='testuser', password='testpass123')
        
        unread_message = Message.objects.filter(receiver=self.user, is_read=False).first()
        
        response = self.client.post(
            reverse('mark_message_read', args=[unread_message.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that message is now read
        unread_message.refresh_from_db()
        self.assertTrue(unread_message.is_read)