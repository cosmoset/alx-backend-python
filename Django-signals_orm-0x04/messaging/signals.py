from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from .models import Message, Notification, MessageHistory
import logging

# Set up logging
logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal handler that logs message content before it's edited.
    """
    if instance.pk:  # Only for existing messages (updates)
        try:
            # Get the original message from database
            original_message = Message.objects.get(pk=instance.pk)
            
            # Check if content has actually changed
            if original_message.content != instance.content:
                # Create history record with old content
                MessageHistory.objects.create(
                    message=original_message,
                    old_content=original_message.content,
                    edited_by=instance.sender,  # Assuming sender is editing
                    edited_at=timezone.now()
                )
                
                # Mark message as edited
                instance.edited = True
                instance.last_edited = timezone.now()
                
                logger.info(
                    f'Message edit logged for message {instance.pk} by {instance.sender.username}'
                )
                
        except Message.DoesNotExist:
            logger.warning(f'Attempted to log edit for non-existent message {instance.pk}')
        except Exception as e:
            logger.error(f'Error logging message edit: {str(e)}')


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler that creates a notification when a new message is created
    or when a message is edited.
    """
    if created:  # New message
        try:
            # Create notification for the receiver
            Notification.objects.create(
                user=instance.receiver,
                message=instance,
                notification_type='message',
                title=f'New message from {instance.sender.username}',
                content=f'{instance.sender.username} sent you a message: "{instance.content[:100]}..."'
                if len(instance.content) > 100 
                else f'{instance.sender.username} sent you a message: "{instance.content}"'
            )
            
            logger.info(
                f'Notification created for {instance.receiver.username} '
                f'about message from {instance.sender.username}'
            )
            
        except Exception as e:
            logger.error(f'Error creating notification: {str(e)}')
    
    elif instance.edited:  # Message was edited
        try:
            # Create notification for the receiver about the edit
            Notification.objects.create(
                user=instance.receiver,
                message=instance,
                notification_type='edit',
                title=f'Message edited by {instance.sender.username}',
                content=f'{instance.sender.username} edited their message to you.'
            )
            
            logger.info(
                f'Edit notification created for {instance.receiver.username} '
                f'about message edit by {instance.sender.username}'
            )
            
        except Exception as e:
            logger.error(f'Error creating edit notification: {str(e)}')


@receiver(post_save, sender=User)
def create_welcome_notification(sender, instance, created, **kwargs):
    """
    Create a welcome notification for new users.
    """
    if created:
        try:
            Notification.objects.create(
                user=instance,
                notification_type='system',
                title='Welcome to our messaging platform!',
                content=f'Hello {instance.username}, welcome to our platform! You can now send and receive messages.'
            )
            
            logger.info(f'Welcome notification created for new user: {instance.username}')
            
        except Exception as e:
            logger.error(f'Error creating welcome notification: {str(e)}')


@receiver(pre_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Log user deletion for audit purposes before actual deletion.
    """
    try:
        # Count related data before deletion
        sent_messages = Message.objects.filter(sender=instance).count()
        received_messages = Message.objects.filter(receiver=instance).count()
        notifications = Notification.objects.filter(user=instance).count()
        message_edits = MessageHistory.objects.filter(edited_by=instance).count()
        
        logger.info(
            f'User {instance.username} (ID: {instance.id}) deletion initiated. '
            f'Related data: {sent_messages} sent messages, {received_messages} received messages, '
            f'{notifications} notifications, {message_edits} message edits'
        )
        
    except Exception as e:
        logger.error(f'Error logging user deletion: {str(e)}')


@receiver(post_delete, sender=User)
def cleanup_user_related_data(sender, instance, **kwargs):
    """
    Clean up any remaining user-related data after user deletion.
    This is a safety net in case CASCADE doesn't handle everything.
    """
    try:
        with transaction.atomic():
            # These should already be deleted by CASCADE, but we'll check for orphans
            
            # Clean up any orphaned notifications (shouldn't exist due to CASCADE)
            orphaned_notifications = Notification.objects.filter(user_id=instance.id)
            if orphaned_notifications.exists():
                count = orphaned_notifications.count()
                orphaned_notifications.delete()
                logger.warning(f'Cleaned up {count} orphaned notifications for user {instance.id}')
            
            # Clean up any orphaned message histories (shouldn't exist due to CASCADE)
            orphaned_histories = MessageHistory.objects.filter(edited_by_id=instance.id)
            if orphaned_histories.exists():
                count = orphaned_histories.count()
                orphaned_histories.delete()
                logger.warning(f'Cleaned up {count} orphaned message histories for user {instance.id}')
            
            # Clean up any orphaned messages (shouldn't exist due to CASCADE)
            orphaned_sent_messages = Message.objects.filter(sender_id=instance.id)
            orphaned_received_messages = Message.objects.filter(receiver_id=instance.id)
            
            if orphaned_sent_messages.exists() or orphaned_received_messages.exists():
                sent_count = orphaned_sent_messages.count()
                received_count = orphaned_received_messages.count()
                orphaned_sent_messages.delete()
                orphaned_received_messages.delete()
                logger.warning(
                    f'Cleaned up {sent_count} orphaned sent messages and '
                    f'{received_count} orphaned received messages for user {instance.id}'
                )
            
            logger.info(f'User {instance.id} deletion cleanup completed successfully')
            
    except Exception as e:
        logger.error(f'Error during user deletion cleanup: {str(e)}')