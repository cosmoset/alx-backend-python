from rest_framework import permissions
from .models import Conversation, Message


class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission class to allow only participants in a conversation 
    to send, view, update and delete messages.
    Only authenticated users can access the API.
    Supports filtering and pagination.
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        Allow filtering and pagination for authenticated users.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user is a participant in the conversation.
        """
        if isinstance(obj, Conversation):
            # For conversation objects, check if user is a participant
            return obj.participants.filter(user_id=request.user.user_id).exists()
        
        elif isinstance(obj, Message):
            # For message objects, check if user is a participant in the conversation
            return obj.conversation.participants.filter(user_id=request.user.user_id).exists()
        
        return False

    def filter_queryset(self, request, queryset, view):
        """
        Filter queryset to only include objects the user has permission to access.
        This method is called during list operations with filtering.
        """
        if hasattr(view, 'get_queryset'):
            # Let the view handle its own queryset filtering
            return view.get_queryset()
        
        return queryset


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.sender == request.user


class IsMessageSender(permissions.BasePermission):
    """
    Custom permission to only allow message senders to modify their messages.
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Only allow the sender to modify their message.
        Must also be participant in the conversation.
        """
        if isinstance(obj, Message):
            # User must be the sender AND a participant in the conversation
            is_sender = obj.sender == request.user
            is_participant = obj.conversation.participants.filter(user_id=request.user.user_id).exists()
            
            # For safe methods (GET, HEAD, OPTIONS), just check participation
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            
            # For write methods, user must be both sender and participant
            return is_sender and is_participant
        
        return False


class CanAccessOwnData(permissions.BasePermission):
    """
    Custom permission to ensure users can only access their own data.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # For User objects, only allow access to own profile
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.user_id
        
        # For other objects, check if user has relationship to the object
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        
        if hasattr(obj, 'participants'):
            return obj.participants.filter(user_id=request.user.user_id).exists()
        
        return False


class ConversationParticipantPermission(permissions.BasePermission):
    """
    Comprehensive permission class for conversation-related operations.
    
    - Users can only see conversations they participate in
    - Users can only create messages in conversations they participate in
    - Users can only modify/delete their own messages
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Conversation):
            # User must be a participant in the conversation
            is_participant = obj.participants.filter(user_id=request.user.user_id).exists()
            
            # For safe methods (GET, HEAD, OPTIONS), just check participation
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            
            # For write methods, also check participation
            # (additional business logic can be added here)
            return is_participant
            
        elif isinstance(obj, Message):
            # User must be a participant in the conversation
            is_participant = obj.conversation.participants.filter(user_id=request.user.user_id).exists()
            
            # For safe methods, just check participation
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            
            # For write methods (PUT, PATCH, DELETE), user must be the sender
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                return obj.sender == request.user and is_participant
            
            # For POST (creating messages), just check participation
            return is_participant
            
        return False


class MessageOwnerPermission(permissions.BasePermission):
    """
    Permission class specifically for message operations.
    
    - Users can only modify/delete their own messages
    - Users can only view messages from conversations they participate in
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Message):
            # Check if user is participant in the conversation
            is_participant = obj.conversation.participants.filter(user_id=request.user.user_id).exists()
            
            if not is_participant:
                return False
            
            # For safe methods, participation is enough
            if request.method in permissions.SAFE_METHODS:
                return True
            
            # For write methods, user must be the sender
            return obj.sender == request.user
            
        return False


class UserProfilePermission(permissions.BasePermission):
    """
    Permission class for user profile operations.
    
    - Users can only view/modify their own profile
    - Admin users can view all profiles
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Superusers can access all profiles
        if request.user.is_superuser:
            return True
            
        # Users can only access their own profile
        return obj.user_id == request.user.user_id


# Utility function to check if user can access conversation
def can_access_conversation(user, conversation):
    """
    Helper function to check if a user can access a conversation.
    
    Args:
        user: The user requesting access
        conversation: The conversation object
        
    Returns:
        bool: True if user can access, False otherwise
    """
    return conversation.participants.filter(user_id=user.user_id).exists()


# Utility function to check if user can modify message
def can_modify_message(user, message):
    """
    Helper function to check if a user can modify a message.
    
    Args:
        user: The user requesting to modify
        message: The message object
        
    Returns:
        bool: True if user can modify, False otherwise
    """
    # User must be the sender and a participant in the conversation
    is_sender = message.sender == user
    is_participant = message.conversation.participants.filter(user_id=user.user_id).exists()
    
    return is_sender and is_participant