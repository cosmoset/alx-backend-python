from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification


@receiver(pre_save, sender=Message)
def log_message_history(sender, instance, **kwargs):
    """
    Logs message edits by:
    1. Checking if message exists (has pk)
    2. Getting original message from database
    3. Comparing content changes
    4. Creating history record if content changed
    5. Updating edited status
    """
    if not instance.pk:  # Skip for new messages
        return

    try:
        original = Message.objects.get(pk=instance.pk)
    except Message.DoesNotExist:
        return  # Message was deleted or doesn't exist

    # Only proceed if content changed
    if original.content == instance.content:
        return

    # Create history record before the message is updated
    MessageHistory.objects.create(message=instance, old_content=original.content)

    # Update message edit flags
    instance.edited = True
    instance.timestamp = timezone.now()  # Update last modified timestamp


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Creates a notification for the receiver when a new message is created.
    """
    if created:
        Notification.objects.create(user=instance.receiver, message=instance)


@receiver(post_delete, sender=User)
def delete_related_data(sender, instance, **kwargs):
    Message.objects.filter(sender=instance).delete()
    Message.objects.filter(receiver=instance).delete()
    Notification.objects.filter(user=instance).delete()
    MessageHistory.objects.filter(edited_by=instance).delete()
