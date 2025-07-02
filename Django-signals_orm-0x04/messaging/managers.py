from django.db import models
from django.db.models import Q


class UnreadMessagesManager(models.Manager):
    """
    Custom manager for filtering unread messages for a specific user.
    Provides optimized queries for unread message operations.
    """
    
    def for_user(self, user):
        """
        Get all unread messages for a specific user (received messages only).
        
        Args:
            user: The User instance to filter messages for
            
        Returns:
            QuerySet: Filtered queryset of unread messages for the user
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).select_related('sender', 'parent_message').only(
            'id', 'content', 'timestamp', 'sender__username', 
            'sender__first_name', 'sender__last_name', 'parent_message__id',
            'parent_message__content', 'edited', 'last_edited'
        )
    
    def unread_count_for_user(self, user):
        """
        Get the count of unread messages for a specific user.
        
        Args:
            user: The User instance to count unread messages for
            
        Returns:
            int: Number of unread messages
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).count()
    
    def unread_threads_for_user(self, user):
        """
        Get unread message threads (root messages only) for a specific user.
        This helps in displaying conversation threads with unread messages.
        
        Args:
            user: The User instance to filter messages for
            
        Returns:
            QuerySet: Filtered queryset of unread root messages
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False,
            parent_message__isnull=True  # Only root messages
        ).select_related('sender').prefetch_related(
            'replies__sender'
        ).only(
            'id', 'content', 'timestamp', 'sender__username',
            'sender__first_name', 'sender__last_name', 'edited'
        )
    
    def mark_thread_as_read(self, user, root_message):
        """
        Mark an entire thread as read for a specific user.
        
        Args:
            user: The User instance
            root_message: The root Message instance of the thread
            
        Returns:
            int: Number of messages marked as read
        """
        # Get all messages in the thread that the user received
        thread_messages = self.get_queryset().filter(
            Q(id=root_message.id) | Q(parent_message=root_message),
            receiver=user,
            is_read=False
        )
        
        # Mark them as read
        updated_count = thread_messages.update(is_read=True)
        return updated_count
    
    def recent_unread(self, user, limit=10):
        """
        Get recent unread messages for a user with a limit.
        
        Args:
            user: The User instance
            limit: Maximum number of messages to return (default: 10)
            
        Returns:
            QuerySet: Recent unread messages
        """
        return self.for_user(user).order_by('-timestamp')[:limit]


class MessageQuerySet(models.QuerySet):
    """
    Custom QuerySet for Message model with additional filtering methods.
    """
    
    def unread(self):
        """Filter for unread messages only."""
        return self.filter(is_read=False)
    
    def read(self):
        """Filter for read messages only."""
        return self.filter(is_read=True)
    
    def for_user_received(self, user):
        """Filter messages received by a specific user."""
        return self.filter(receiver=user)
    
    def for_user_sent(self, user):
        """Filter messages sent by a specific user."""
        return self.filter(sender=user)
    
    def threads_only(self):
        """Filter for root messages only (not replies)."""
        return self.filter(parent_message__isnull=True)
    
    def replies_only(self):
        """Filter for reply messages only."""
        return self.filter(parent_message__isnull=False)
    
    def optimized_for_listing(self):
        """Optimize query for message listing views."""
        return self.select_related(
            'sender', 'receiver', 'parent_message'
        ).only(
            'id', 'content', 'timestamp', 'is_read', 'edited',
            'sender__username', 'receiver__username', 
            'parent_message__id', 'parent_message__content'
        )


class MessageManager(models.Manager):
    """
    Default manager for Message model with custom QuerySet.
    """
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return MessageQuerySet(self.model, using=self._db)
    
    def unread(self):
        """Get unread messages."""
        return self.get_queryset().unread()
    
    def read(self):
        """Get read messages."""
        return self.get_queryset().read()
    
    def for_user_received(self, user):
        """Get messages received by user."""
        return self.get_queryset().for_user_received(user)
    
    def for_user_sent(self, user):
        """Get messages sent by user."""
        return self.get_queryset().for_user_sent(user)
    
    def threads_only(self):
        """Get thread root messages only."""
        return self.get_queryset().threads_only()
    
    def optimized_for_listing(self):
        """Get optimized queryset for listing."""
        return self.get_queryset().optimized_for_listing()