# views.py
from rest_framework import viewsets, status, filters, generics, permissions 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch

from chats.permissions import IsParticipant
from .models import Conversation, Message, ConversationParticipant, MessageReaction
from .serializers import (
    ConversationSerializer, 
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer, 
    MessageCreateSerializer,
    MessageReactionCreateSerializer,
    ConversationParticipantSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserMinimalSerializer, 
)

# JWT customization and User Views
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers as drf_serializers 
from django.contrib.auth import get_user_model

User = get_user_model()

# JWT Customization
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
   
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email
        token['username'] = user.username
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_online'] = user.is_online
        token['user_id'] = str(user.user_id)
        return token

class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view to use our MyTokenObtainPairSerializer.
    This will be used if you decide to replace the default simplejwt TokenObtainPairView.
    """
    serializer_class = MyTokenObtainPairSerializer


# User Registration View
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)

    class RegisterSerializer(UserProfileSerializer):
        password = drf_serializers.CharField(write_only=True) 

        class Meta(UserProfileSerializer.Meta):
            fields = UserProfileSerializer.Meta.fields + ['password']
            read_only_fields = ['user_id', 'created_at', 'last_seen', 'updated_at']

        def create(self, validated_data):
          
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                phone_number=validated_data.get('phone_number'),
                bio=validated_data.get('bio', '')
            )
            return user
    serializer_class = RegisterSerializer


# User Profile View (for the currently authenticated user)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserListView(viewsets.ReadOnlyModelViewSet): 
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'user_id' 

class UserDetailView(generics.RetrieveAPIView): 
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'user_id' 
    permission_classes = (permissions.IsAuthenticated,)

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations
    Provides CRUD operations for conversations with participant filtering
    """
    permission_classes = [IsAuthenticated, IsParticipant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter] 
    filterset_fields = ['conversation_type', 'is_active']
    search_fields = ['conversation_participants__user__username'] 
    ordering_fields = ['updated_at', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer
    
    def get_queryset(self):
        """
        Filter conversations to show only those the user participates in
        with optimized prefetching for performance
        """
        return Conversation.objects.filter(
            conversation_participants__user=self.request.user,
            conversation_participants__is_active=True,
            is_active=True
        ).select_related('created_by').prefetch_related(
            'conversation_participants__user',
            'messages'
        ).distinct().order_by('-updated_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new conversation with proper context"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        

        if serializer.validated_data.get('conversation_type') == 'direct':
            participant_ids = serializer.validated_data.get('participant_ids', [])
            if participant_ids:
                existing_conversation = Conversation.objects.filter(
                    conversation_type='direct',
                    conversation_participants__user=request.user,
                    is_active=True
                ).filter(
                    conversation_participants__user__user_id=participant_ids[0]
                ).first()
                
                if existing_conversation:
                    # Return existing conversation instead of creating new one
                    return Response(
                        ConversationSerializer(existing_conversation, context={'request': request}).data,
                        status=status.HTTP_200_OK
                    )
        
        conversation = serializer.save()
        return Response(
            ConversationSerializer(conversation, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get paginated messages for a specific conversation
        """
        conversation = self.get_object()
        self.check_object_permissions(request, conversation)

        
        # Mark messages as read
        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user
        ).first()
        
        if participant:
            participant.mark_as_read()
        
        # Get messages with pagination support
        page = request.query_params.get('page', 1)
        limit = min(int(request.query_params.get('limit', 50)), 100) 
        offset = (int(page) - 1) * limit
        
        messages = conversation.messages.filter(
            is_deleted=False
        ).select_related('sender', 'reply_to__sender').prefetch_related(
            'message_reactions__user'
        ).order_by('-sent_at')[offset:offset + limit]
        
        serializer = MessageSerializer(
            messages, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a message to a specific conversation
        """
        conversation = self.get_object()
        self.check_object_permissions(request, conversation)

        # Check if user is an active participant
        # participant = ConversationParticipant.objects.filter(
        #     conversation=conversation,
        #     user=request.user,
        #     is_active=True
        # ).first()
        
        # if not participant:
        #     return Response(
        #         {'error': 'You are not an active participant in this conversation'}, 
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        
        serializer = MessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save(
                sender=request.user,
                conversation=conversation
            )
            
            # Update conversation's updated_at timestamp
            conversation.save(update_fields=['updated_at'])
            
            # Return the created message with full details
            message_serializer = MessageSerializer(message, context={'request': request})
            return Response(message_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # @action(detail=True, methods=['post'])
    # def add_participant(self, request, pk=None):
    #     """
    #     Add a participant to a group conversation (owner/admin only)
    #     """
    #     conversation = self.get_object()
    #     self.check_object_permissions(request, conversation)

        
       
    #     participant = ConversationParticipant.objects.filter(
    #         conversation=conversation,
    #         user=request.user,
    #         role__in=['owner', 'admin']
    #     ).first()

    #     if not participant:
    #         return Response(
    #             {'error': 'You do not have permission to add participants'}, 
    #             status=status.HTTP_403_FORBIDDEN
    #         )
        
        
    #     user_id = request.data.get('user_id')
    #     if not user_id:
    #         return Response(
    #             {'error': 'user_id is required'}, 
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
        
    #     try:
    #         from django.contrib.auth import get_user_model
    #         User = get_user_model()
    #         user = User.objects.get(user_id=user_id)
            
            
    #         if ConversationParticipant.objects.filter(
    #             conversation=conversation,
    #             user=user
    #         ).exists():
    #             return Response(
    #                 {'error': 'User is already a participant'}, 
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
            
            
    #         new_participant = ConversationParticipant.objects.create(
    #             conversation=conversation,
    #             user=user,
    #             role='member'
    #         )
            
    #         serializer = ConversationParticipantSerializer(new_participant)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
            
    #     except User.DoesNotExist:
    #         return Response(
    #             {'error': 'User not found'}, 
    #             status=status.HTTP_404_NOT_FOUND
    #         )
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        conversation = self.get_object()

        self.check_object_permissions(request, conversation)

        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user,
            role__in=['owner', 'admin']
        ).first()

        if not participant:
            return Response(
                {'error': 'You do not have permission to add participants'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(user_id=user_id)

            if ConversationParticipant.objects.filter(conversation=conversation, user=user).exists():
                return Response({'error': 'User is already a participant'}, status=status.HTTP_400_BAD_REQUEST)

            new_participant = ConversationParticipant.objects.create(
                conversation=conversation,
                user=user,
                role='member'
            )

            serializer = ConversationParticipantSerializer(new_participant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


        @action(detail=True, methods=['post'])
        def leave(self, request, pk=None):
            """
            Leave a conversation (mark participant as inactive)
            """
            conversation = self.get_object()
            self.check_object_permissions(request, conversation)

            
            participant = ConversationParticipant.objects.filter(
                conversation=conversation,
                user=request.user,
            )
            
            participant.is_active = False
            participant.save()
            
            return Response({'message': 'Successfully left the conversation'})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages
    Provides CRUD operations for messages with conversation filtering
    """
    permission_classes = [IsAuthenticated, IsParticipant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['conversation', 'is_deleted']
    search_fields = ['message_body']
    ordering_fields = ['sent_at', 'updated_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """
        Filter messages to show only those in conversations the user participates in
        """
        return Message.objects.filter(
            conversation__conversation_participants__user=self.request.user,
            conversation__conversation_participants__is_active=True,
            is_deleted=False
        ).select_related('sender', 'conversation', 'reply_to__sender').prefetch_related(
            'message_reactions__user'
        ).distinct().order_by('-sent_at')
    
    def perform_create(self, serializer):
        """
        Set the sender as the current user and validate conversation access
        """
        conversation = serializer.validated_data['conversation']

        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=self.request.user,
            is_active=True
        ).first()
        
        if not participant:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError(
                'You are not an active participant in this conversation'
            )
        
        message = serializer.save(sender=self.request.user)
        
        # Update conversation's updated_at timestamp
        conversation.save(update_fields=['updated_at'])
        
        return message
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """
        Add or toggle a reaction to a message
        """
        
        message = self.get_object()
        self.check_object_permissions(request, message)
        
        serializer = MessageReactionCreateSerializer(
            data=request.data,
            context={'message': message, 'request': request}
        )
        
        if serializer.is_valid():
            # Check if reaction already exists
            existing_reaction = MessageReaction.objects.filter(
                message=message,
                user=request.user,
                reaction_type=serializer.validated_data['reaction_type']
            ).first()
            
            if existing_reaction:
                # Remove existing reaction (toggle off)
                existing_reaction.delete()
                return Response({'message': 'Reaction removed'})
            else:
                # Add new reaction
                reaction = serializer.save()
                return Response(
                    MessageReactionCreateSerializer(reaction).data,
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """
        Edit a message (only by sender)
        """
        message = self.get_object()
        self.check_object_permissions(request, message)
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_body = request.data.get('message_body')
        if not new_body or not new_body.strip():
            return Response(
                {'error': 'Message body cannot be empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.message_body = new_body
        message.is_edited = True
        message.save(update_fields=['message_body', 'is_edited', 'edited_at', 'updated_at'])
        
        serializer = MessageSerializer(message, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """
        Soft delete a message (only by sender)
        """
        message = self.get_object()
        self.check_object_permissions(request, message)
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_deleted = True
        message.save(update_fields=['is_deleted', 'updated_at'])
        
        return Response({'message': 'Message deleted successfully'})
    
    @action(detail=False, methods=['get'])
    def by_conversation(self, request):
        """
        Get messages filtered by conversation ID with pagination
        """
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response(
                {'error': 'conversation_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
       

        conversation = get_object_or_404(
            Conversation.objects.filter(
                conversation_participants__user=request.user,
                conversation_participants__is_active=True
            ),
            conversation_id=conversation_id
        )
        
        self.check_object_permissions(request, conversation)

        participant = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user
        ).first()
        
        if participant:
            participant.mark_as_read()
        
        queryset = self.get_queryset().filter(conversation=conversation).order_by('-sent_at')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
       
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
