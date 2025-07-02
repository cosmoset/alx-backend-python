from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Conversation, Message
from .serializers import (
    UserSerializer,
    ConversationSerializer,
    ConversationListSerializer,
    MessageSerializer,
    MessageCreateSerializer
)
from .permissions import (
    IsParticipantOfConversation,
    IsMessageSender,
    UserProfilePermission,
    CanAccessOwnData
)
from .filters import MessageFilter, ConversationFilter, UserFilter
from .pagination import MessagePagination, ConversationPagination, UserPagination


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    Provides CRUD operations for user management with proper permissions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, UserProfilePermission]
    lookup_field = 'user_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['first_name', 'last_name', 'email', 'created_at']
    pagination_class = UserPagination

    def get_queryset(self):
        """
        Users can only see their own profile unless they are superusers.
        """
        if self.request.user.is_superuser:
            queryset = User.objects.all()
        else:
            # Regular users can only see their own profile
            queryset = User.objects.filter(user_id=self.request.user.user_id)
        
        # Optional filtering
        email = self.request.query_params.get('email')
        name = self.request.query_params.get('name')
        
        if email and self.request.user.is_superuser:
            queryset = queryset.filter(email__icontains=email)
        if name and self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(first_name__icontains=name) | Q(last_name__icontains=name)
            )
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Prevent user creation through this endpoint.
        Users should register through the auth endpoints.
        """
        return Response(
            {'error': 'User creation not allowed through this endpoint. Use /api/auth/register/'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        """
        Allow users to update only their own profile.
        """
        instance = self.get_object()
        if instance.user_id != request.user.user_id and not request.user.is_superuser:
            return Response(
                {'error': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Allow users to delete only their own profile.
        """
        instance = self.get_object()
        if instance.user_id != request.user.user_id and not request.user.is_superuser:
            return Response(
                {'error': 'You can only delete your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    Users can only access conversations they participate in.
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    lookup_field = 'conversation_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ConversationFilter
    search_fields = ['participants__first_name', 'participants__last_name', 'participants__email']
    ordering_fields = ['created_at', 'updated_at']
    pagination_class = ConversationPagination

    def get_queryset(self):
        """
        Return only conversations where the current user is a participant.
        """
        return Conversation.objects.filter(
            participants=self.request.user
        ).distinct().order_by('-updated_at')

    def get_serializer_class(self):
        """
        Return different serializers for list and detail views.
        """
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new conversation.
        Automatically adds the current user as a participant.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the conversation
        conversation = serializer.save()
        
        # Add the current user as a participant if not already included
        if not conversation.participants.filter(user_id=request.user.user_id).exists():
            conversation.participants.add(request.user)
        
        # Return the created conversation with full serializer
        response_serializer = ConversationSerializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, conversation_id=None):
        """
        Add a participant to an existing conversation.
        Only existing participants can add new participants.
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id)
            if conversation.participants.filter(user_id=user_id).exists():
                return Response(
                    {'error': 'User is already a participant'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            conversation.participants.add(user)
            return Response(
                {'message': f'User {user.first_name} added to conversation'}, 
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, conversation_id=None):
        """
        Remove a participant from an existing conversation.
        Users can remove themselves or participants can remove others.
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id)
            if not conversation.participants.filter(user_id=user_id).exists():
                return Response(
                    {'error': 'User is not a participant in this conversation'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there will be at least one participant left
            if conversation.participants.count() <= 1:
                return Response(
                    {'error': 'Cannot remove the last participant from conversation'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            conversation.participants.remove(user)
            return Response(
                {'message': f'User {user.first_name} removed from conversation'}, 
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def messages(self, request, conversation_id=None):
        """
        Get all messages for a specific conversation.
        Only participants can access messages.
        """
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('sent_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    Users can only access messages from conversations they participate in.
    Implements pagination (20 messages per page) and filtering.
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation, IsMessageSender]
    lookup_field = 'message_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MessageFilter
    search_fields = ['message_body', 'sender__first_name', 'sender__last_name', 'sender__email']
    ordering_fields = ['sent_at', 'sender__first_name']
    pagination_class = MessagePagination

    def get_queryset(self):
        """
        Return messages from conversations where the current user is a participant.
        """
        user_conversations = Conversation.objects.filter(
            participants=self.request.user
        )
        return Message.objects.filter(
            conversation__in=user_conversations
        ).order_by('-sent_at')

    def get_serializer_class(self):
        """
        Return different serializers for create and other actions.
        """
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new message.
        Automatically sets the sender to the current user.
        Validates that user is a participant in the conversation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the conversation
        conversation = serializer.validated_data.get('conversation')
        
        # Check if user is a participant in the conversation
        if not conversation.participants.filter(user_id=request.user.user_id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Set the sender to current user
        message = serializer.save(sender=request.user)
        
        # Return the created message with full serializer
        response_serializer = MessageSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """
        List messages with optional conversation filtering.
        """
        queryset = self.get_queryset()
        conversation_id = request.query_params.get('conversation_id')
        
        if conversation_id:
            # Filter messages by conversation
            try:
                conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    participants=request.user
                )
                queryset = queryset.filter(conversation=conversation)
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found or you are not a participant'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """
        Send a message to an existing conversation.
        Convenient endpoint for sending messages.
        """
        conversation_id = request.data.get('conversation_id')
        message_body = request.data.get('message_body')
        
        if not conversation_id or not message_body:
            return Response(
                {'error': 'conversation_id and message_body are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = Conversation.objects.get(
                conversation_id=conversation_id,
                participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found or you are not a participant'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            conversation=conversation,
            message_body=message_body
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, message_id=None):
        """
        Mark a message as read (placeholder for future implementation).
        """
        message = self.get_object()
        # In a real application, you might have a read_status field
        # For now, we'll just return success
        return Response(
            {'message': 'Message marked as read'}, 
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        """
        Update a message (only sender can update their own messages).
        """
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only update your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a message (only sender can delete their own messages).
        """
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)