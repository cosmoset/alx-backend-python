"""
Context processors for the messaging app.
These make certain variables available in all templates.
"""

from .models import Message, Notification


def messaging_context(request):
    """
    Add messaging-related context variables to all templates.
    """
    context = {
        'global_unread_count': 0,
        'global_notification_count': 0,
    }
    
    if request.user.is_authenticated:
        try:
            # Get unread message count
            context['global_unread_count'] = Message.unread_messages.unread_count_for_user(request.user)
            
            # Get unread notification count
            context['global_notification_count'] = Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
        except Exception:
            # Fail silently if there are any database issues
            pass
    
    return context