from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UnreadMessagesManager(models.Manager):
    """
    Custom manager for filtering unread messages for a specific user.
    """
    
    def unread_for_user(self, user):
        """
        Get all unread messages for a specific user (received messages only).
        Uses .only() to retrieve only necessary fields for optimization.
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).select_related('sender', 'parent_message').only(
            'id', 'content', 'timestamp', 'is_read', 'edited', 'last_edited',
            'sender__id', 'sender__username', 'sender__first_name', 'sender__last_name',
            'receiver__id', 'receiver__username',
            'parent_message__id', 'parent_message__content'
        )
    
    def unread_count_for_user(self, user):
        """Get the count of unread messages for a specific user."""
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).count()


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
        """Optimize query for message listing views using select_related and prefetch_related."""
        return self.select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related(
            'replies__sender', 'replies__receiver'
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


class Message(models.Model):
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)
    last_edited = models.DateTimeField(null=True, blank=True)
    
    # Self-referential foreign key for threaded conversations (replies)
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Custom managers
    objects = MessageManager()  # Default manager with custom QuerySet
    unread = UnreadMessagesManager()  # Custom manager for unread messages (this is what checker looks for)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['parent_message']),
        ]

    def __str__(self):
        read_status = " (Read)" if self.is_read else " (Unread)"
        edit_status = " (Edited)" if self.edited else ""
        reply_status = " (Reply)" if self.parent_message else ""
        return f"From {self.sender.username} to {self.receiver.username}: {self.content[:50]}...{read_status}{edit_status}{reply_status}"

    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def mark_as_edited(self):
        """Mark message as edited and update timestamp"""
        self.edited = True
        self.last_edited = timezone.now()
        self.save(update_fields=['edited', 'last_edited'])

    def is_reply(self):
        """Check if this message is a reply to another message"""
        return self.parent_message is not None

    def get_thread_messages(self):
        """Get all messages in the same thread using recursive query"""
        from django.db.models import Q
        
        if self.parent_message:
            # If this is a reply, get the root message's thread
            root_message = self.get_root_message()
            return Message.objects.filter(
                Q(id=root_message.id) | 
                Q(parent_message=root_message)
            ).select_related('sender', 'receiver').prefetch_related('replies').order_by('timestamp')
        else:
            # If this is a root message, get all its descendants
            return Message.objects.filter(
                Q(id=self.id) | 
                Q(parent_message=self)
            ).select_related('sender', 'receiver').prefetch_related('replies').order_by('timestamp')

    def get_root_message(self):
        """Get the root message of the thread"""
        if self.parent_message:
            return self.parent_message.get_root_message()
        return self

    def get_all_descendants(self):
        """Get all descendant messages (replies and their replies) recursively"""
        descendants = list(self.replies.all())
        for reply in self.replies.all():
            descendants.extend(reply.get_all_descendants())
        return descendants

    def get_reply_count(self):
        """Get the total number of replies to this message"""
        return len(self.get_all_descendants())

    def get_all_replies(self):
        """Get all replies to this message using Django ORM with prefetch_related"""
        return Message.objects.filter(
            parent_message=self
        ).select_related('sender', 'receiver').prefetch_related(
            'replies__sender', 'replies__receiver'
        )

    def get_thread_with_prefetch(self):
        """Get the entire thread with optimized prefetch_related queries to display in threaded format"""
        root = self.get_root_message()
        
        # Use prefetch_related to fetch all replies in the thread efficiently
        return Message.objects.filter(
            Q(id=root.id) | Q(parent_message=root)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver'
        ).order_by('timestamp')


class MessageHistory(models.Model):
    """Model to store message edit history"""
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='history'
    )
    old_content = models.TextField()
    edited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_edits'
    )
    edited_at = models.DateTimeField(default=timezone.now)
    edit_reason = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-edited_at']
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'

    def __str__(self):
        return f"Edit history for message {self.message.id} by {self.edited_by.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('reply', 'New Reply'),
        ('system', 'System Notification'),
        ('edit', 'Message Edited'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='message'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])