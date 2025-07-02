from rest_framework import serializers
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Handles user data serialization and validation.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'user_id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number', 
            'password',
            'created_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'user_id': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)  # This encrypts the password
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Update user instance, handling password encryption if provided.
        """
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)  # Encrypt the new password
        
        instance.save()
        return instance


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    Includes sender information and handles nested relationships.
    """
    sender = UserSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Message
        fields = [
            'message_id',
            'sender',
            'sender_id',
            'conversation',
            'message_body',
            'sent_at'
        ]
        extra_kwargs = {
            'message_id': {'read_only': True},
            'sent_at': {'read_only': True},
        }

    def validate_sender_id(self, value):
        """
        Validate that the sender exists.
        """
        try:
            User.objects.get(user_id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Sender does not exist.")
        return value

    def create(self, validated_data):
        """
        Create a new message, setting the sender from sender_id.
        """
        sender_id = validated_data.pop('sender_id')
        sender = User.objects.get(user_id=sender_id)
        validated_data['sender'] = sender
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model.
    Handles many-to-many relationships with participants and nested messages.
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    messages = MessageSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participants',
            'participant_ids',
            'messages',
            'participant_count',
            'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'conversation_id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def get_participant_count(self, obj):
        """
        Return the number of participants in the conversation.
        """
        return obj.participants.count()

    def validate_participant_ids(self, value):
        """
        Validate that all participant IDs exist and there are at least 2 participants.
        """
        if len(value) < 2:
            raise serializers.ValidationError("A conversation must have at least 2 participants.")
        
        # Check if all users exist
        existing_users = User.objects.filter(user_id__in=value)
        if existing_users.count() != len(value):
            raise serializers.ValidationError("One or more participant IDs are invalid.")
        
        return value

    def create(self, validated_data):
        """
        Create a new conversation and add participants.
        """
        participant_ids = validated_data.pop('participant_ids', [])
        conversation = Conversation.objects.create(**validated_data)
        
        if participant_ids:
            participants = User.objects.filter(user_id__in=participant_ids)
            conversation.participants.set(participants)
        
        return conversation

    def update(self, instance, validated_data):
        """
        Update conversation and handle participant changes.
        """
        participant_ids = validated_data.pop('participant_ids', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update participants if provided
        if participant_ids is not None:
            participants = User.objects.filter(user_id__in=participant_ids)
            instance.participants.set(participants)
        
        instance.save()
        return instance


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing conversations without nested messages.
    Used for performance optimization in list views.
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participants',
            'participant_count',
            'last_message',
            'created_at',
            'updated_at'
        ]

    def get_participant_count(self, obj):
        """
        Return the number of participants in the conversation.
        """
        return obj.participants.count()

    def get_last_message(self, obj):
        """
        Return the most recent message in the conversation.
        """
        last_message = obj.messages.last()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'sender': last_message.sender.first_name,
                'message_body': last_message.message_body,
                'sent_at': last_message.sent_at
            }
        return None


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating messages.
    Used to avoid circular imports and optimize message creation.
    """
    class Meta:
        model = Message
        fields = [
            'sender',
            'conversation',
            'message_body'
        ]

    def validate(self, data):
        """
        Validate that the sender is a participant in the conversation.
        """
        sender = data.get('sender')
        conversation = data.get('conversation')
        
        if sender and conversation:
            if not conversation.participants.filter(user_id=sender.user_id).exists():
                raise serializers.ValidationError(
                    "Sender must be a participant in the conversation."
                )
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password confirmation.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'user_id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number', 
            'password',
            'password_confirm',
            'created_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True},
            'user_id': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def validate(self, data):
        """
        Check that the two password entries match.
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        validated_data.pop('password_confirm')  # Remove password_confirm
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, data):
        """
        Check that the two new password entries match.
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read-only sensitive info).
    """
    class Meta:
        model = User
        fields = [
            'user_id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number', 
            'created_at',
            'last_login',
            'is_active'
        ]
        read_only_fields = [
            'user_id', 
            'username', 
            'created_at',
            'last_login',
            'is_active'
        ]