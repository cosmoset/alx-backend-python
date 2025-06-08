# chats/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import User, Conversation, ConversationParticipant, Message, MessageReaction

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Basic User serializer for general user information
    """
    full_name = serializers.CharField(read_only=True)
    is_online_status = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'phone_number', 'profile_picture', 'bio', 
            'is_online', 'is_online_status', 'last_seen', 'created_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'last_seen']
    
    def to_representation(self, instance):
        """
        Override to populate computed fields using SerializerMethodField logic
        """
        data = super().to_representation(instance)
        
        # Populate full_name
        full_name = instance.get_full_name()
        data['full_name'] = full_name if full_name.strip() else instance.username
        
        # Populate is_online_status
        if instance.is_online:
            data['is_online_status'] = "online"
        else:
            # Consider user online if last seen within 5 minutes
            time_threshold = timezone.now() - timezone.timedelta(minutes=5)
            if instance.last_seen and instance.last_seen > time_threshold:
                data['is_online_status'] = "recently_active"
            else:
                data['is_online_status'] = "offline"
        
        return data


class UserProfileSerializer(UserSerializer):
    """
    Extended User serializer for profile management (includes sensitive fields)
    """
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['updated_at']
        read_only_fields = UserSerializer.Meta.read_only_fields + ['updated_at']


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal User serializer for nested relationships (reduces payload size)
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'username', 'first_name', 'last_name', 'full_name', 'profile_picture', 'is_online']
        read_only_fields = ['user_id']
    
    def to_representation(self, instance):
        """
        Override to populate computed fields
        """
        data = super().to_representation(instance)
        
        # Populate full_name
        full_name = instance.get_field_names()
        data['full_name'] = full_name if full_name.strip() else instance.username
        
        return data


class MessageReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for message reactions
    """
    user = UserMinimalSerializer(read_only=True)
    reaction_emoji = serializers.CharField(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'reaction_type', 'reaction_emoji', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def to_representation(self, instance):
        """
        Override to populate computed fields
        """
        data = super().to_representation(instance)
        
        # Populate reaction_emoji
        data['reaction_emoji'] = dict(MessageReaction.REACTION_TYPES).get(instance.reaction_type, '')
        
        return data


class MessageSerializer(serializers.ModelSerializer):
    """
    Main Message serializer with nested relationships
    """
    sender = UserMinimalSerializer(read_only=True)
    reply_to_message = serializers.DictField(read_only=True)
    reactions = MessageReactionSerializer(source='message_reactions', many=True, read_only=True)
    reaction_summary = serializers.DictField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    file_url = serializers.CharField(read_only=True, allow_null=True)
    is_own_message = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'message_type', 'message_body', 
            'file_attachment', 'file_url', 'reply_to', 'reply_to_message',
            'is_edited', 'edited_at', 'is_deleted', 'sent_at', 'updated_at',
            'reactions', 'reaction_summary', 'replies_count', 'is_own_message'
        ]
        read_only_fields = [
            'message_id', 'sent_at', 'updated_at', 'is_edited', 
            'edited_at', 'is_deleted'
        ]
    
    def to_representation(self, instance):
        """
        Override to populate all computed fields for messages
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Populate reply_to_message
        if instance.reply_to and not instance.reply_to.is_deleted:
            data['reply_to_message'] = {
                'message_id': instance.reply_to.message_id,
                'sender': UserMinimalSerializer(instance.reply_to.sender).data,
                'message_type': instance.reply_to.message_type,
                'message_body': instance.reply_to.message_body[:100] + "..." if len(instance.reply_to.message_body) > 100 else instance.reply_to.message_body,
                'sent_at': instance.reply_to.sent_at
            }
        else:
            data['reply_to_message'] = None
        
        # Populate reaction_summary
        reactions = instance.message_reactions.all()
        summary = {}
        for reaction in reactions:
            reaction_type = reaction.reaction_type
            if reaction_type not in summary:
                summary[reaction_type] = {
                    'count': 0,
                    'emoji': dict(MessageReaction.REACTION_TYPES).get(reaction_type, ''),
                    'users': []
                }
            summary[reaction_type]['count'] += 1
            summary[reaction_type]['users'].append(reaction.user.username)
        data['reaction_summary'] = summary
        
        # Populate replies_count
        data['replies_count'] = instance.replies.filter(is_deleted=False).count()
        
        # Populate file_url
        if instance.file_attachment:
            if request:
                data['file_url'] = request.build_absolute_uri(instance.file_attachment.url)
            else:
                data['file_url'] = instance.file_attachment.url
        else:
            data['file_url'] = None
        
        # Populate is_own_message
        if request and request.user.is_authenticated:
            data['is_own_message'] = instance.sender == request.user
        else:
            data['is_own_message'] = False
        
        return data


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new messages
    """
    class Meta:
        model = Message
        fields = [
            'message_type', 'message_body', 'file_attachment', 'reply_to'
        ]
    
    def validate(self, data):
        """Validate message data"""
        message_type = data.get('message_type', 'text')
        message_body = data.get('message_body', '')
        file_attachment = data.get('file_attachment')
        
        # Text messages must have content
        if message_type == 'text' and not message_body.strip():
            raise serializers.ValidationError("Text messages cannot be empty.")
        
        # File messages must have attachments
        if message_type in ['image', 'file', 'audio', 'video'] and not file_attachment:
            raise serializers.ValidationError(f"{message_type.title()} messages must include a file attachment.")
        
        return data


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for conversation participants
    """
    user = UserMinimalSerializer(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'id', 'user', 'role', 'joined_at', 'last_read_at', 
            'is_muted', 'is_active', 'unread_count'
        ]
        read_only_fields = ['id', 'joined_at']
    
    def to_representation(self, instance):
        """
        Override to populate computed fields
        """
        data = super().to_representation(instance)
        
        # Populate unread_count
        data['unread_count'] = instance.conversation.messages.filter(
            sent_at__gt=instance.last_read_at,
            is_deleted=False
        ).exclude(sender=instance.user).count()
        
        return data


class ConversationSerializer(serializers.ModelSerializer):
    """
    Main Conversation serializer with nested relationships
    """
    participants = ConversationParticipantSerializer(
        source='conversation_participants', 
        many=True, 
        read_only=True
    )
    created_by = UserMinimalSerializer(read_only=True)
    last_message = serializers.DictField(read_only=True, allow_null=True)
    unread_count = serializers.IntegerField(read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    display_image = serializers.CharField(read_only=True, allow_null=True)
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'title', 'conversation_type', 'participants',
            'created_by', 'created_at', 'updated_at', 'is_active',
            'last_message', 'unread_count', 'participant_count',
            'display_name', 'display_image'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """
        Override to populate all computed fields for conversations
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Populate last_message
        last_message = instance.get_last_message()
        if last_message:
            data['last_message'] = {
                'message_id': last_message.message_id,
                'sender': UserMinimalSerializer(last_message.sender).data,
                'message_type': last_message.message_type,
                'message_body': last_message.message_body[:100] + "..." if len(last_message.message_body) > 100 else last_message.message_body,
                'sent_at': last_message.sent_at,
                'is_deleted': last_message.is_deleted
            }
        else:
            data['last_message'] = None
        
        # Populate unread_count
        if request and request.user.is_authenticated:
            data['unread_count'] = instance.get_unread_count(request.user)
        else:
            data['unread_count'] = 0
        
        # Populate participant_count
        data['participant_count'] = instance.conversation_participants.filter(is_active=True).count()
        
        # Populate display_name
        if instance.conversation_type == 'group' and instance.title:
            data['display_name'] = instance.title
        elif request and request.user.is_authenticated and instance.conversation_type == 'direct':
            other_participant = instance.participants.exclude(user_id=request.user.user_id).first()
            if other_participant:
                full_name = other_participant.get_full_name()
                data['display_name'] = full_name if full_name.strip() else other_participant.username
            else:
                data['display_name'] = f"Conversation {str(instance.conversation_id)[:8]}"
        else:
            data['display_name'] = f"Conversation {str(instance.conversation_id)[:8]}"
        
        # Populate display_image
        if request and request.user.is_authenticated and instance.conversation_type == 'direct':
            other_participant = instance.participants.exclude(user_id=request.user.user_id).first()
            if other_participant and other_participant.profile_picture:
                data['display_image'] = request.build_absolute_uri(other_participant.profile_picture.url)
            else:
                data['display_image'] = None
        else:
            data['display_image'] = None
        
        return data


class ConversationDetailSerializer(ConversationSerializer):
    """
    Detailed Conversation serializer that includes recent messages
    """
    recent_messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['recent_messages']
    
    def to_representation(self, instance):
        """
        Override to populate recent_messages
        """
        data = super().to_representation(instance)
        
        # Populate recent_messages
        recent_messages = instance.messages.filter(is_deleted=False)[:20]
        data['recent_messages'] = MessageSerializer(
            recent_messages, 
            many=True, 
            context=self.context
        ).data
        
        return data


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new conversations
    """
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Conversation
        fields = ['title', 'conversation_type', 'participant_ids']
    
    def validate(self, data):
        """Validate conversation creation data"""
        conversation_type = data.get('conversation_type', 'direct')
        participant_ids = data.get('participant_ids', [])
        
        if conversation_type == 'direct' and len(participant_ids) != 1:
            raise serializers.ValidationError(
                "Direct messages must have exactly one other participant."
            )
        
        if conversation_type == 'group' and len(participant_ids) < 1:
            raise serializers.ValidationError(
                "Group conversations must have at least one other participant."
            )
        
        # Validate that all participant IDs exist
        existing_users = User.objects.filter(user_id__in=participant_ids)
        if len(existing_users) != len(participant_ids):
            raise serializers.ValidationError(
                "One or more participant IDs are invalid."
            )
        
        return data
    
    def create(self, validated_data):
        """Create a new conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', [])
        request = self.context.get('request')
        
        # Create the conversation
        conversation = Conversation.objects.create(
            created_by=request.user,
            **validated_data
        )
        
        # Add the creator as a participant
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user,
            role='owner' if validated_data.get('conversation_type') == 'group' else 'member'
        )
        
        # Add other participants
        for user_id in participant_ids:
            user = User.objects.get(user_id=user_id)
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=user,
                role='member'
            )
        
        return conversation


class MessageReactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating message reactions
    """
    class Meta:
        model = MessageReaction
        fields = ['reaction_type']
    
    def create(self, validated_data):
        """Create or update a message reaction"""
        message = self.context['message']
        user = self.context['request'].user
        
        # Remove existing reaction of the same type if it exists
        MessageReaction.objects.filter(
            message=message,
            user=user,
            reaction_type=validated_data['reaction_type']
        ).delete()
        
        # Create new reaction
        return MessageReaction.objects.create(
            message=message,
            user=user,
            **validated_data
        )
