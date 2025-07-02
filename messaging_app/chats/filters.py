import django_filters
from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Message, Conversation, User


class MessageFilter(django_filters.FilterSet):
    """
    Filter class for Message model to retrieve messages within a time range
    and filter by conversation participants.
    """
    
    # Date range filtering
    sent_after = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte')
    sent_before = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='lte')
    sent_date = django_filters.DateFilter(field_name='sent_at__date')
    
    # Time range filtering (alternative)
    date_from = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='lte')
    
    # Conversation filtering
    conversation_id = django_filters.UUIDFilter(field_name='conversation__conversation_id')
    
    # Sender filtering
    sender_id = django_filters.UUIDFilter(field_name='sender__user_id')
    sender_email = django_filters.CharFilter(field_name='sender__email', lookup_expr='icontains')
    sender_name = django_filters.CharFilter(method='filter_by_sender_name')
    
    # Message content filtering
    message_content = django_filters.CharFilter(field_name='message_body', lookup_expr='icontains')
    
    # Participants filtering (messages from conversations with specific users)
    with_user = django_filters.UUIDFilter(method='filter_conversations_with_user')
    with_user_email = django_filters.CharFilter(method='filter_conversations_with_user_email')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('sent_at', 'sent_at'),
            ('sender__first_name', 'sender_name'),
            ('conversation__updated_at', 'conversation_updated'),
        ),
        field_labels={
            'sent_at': 'Date Sent',
            'sender_name': 'Sender Name',
            'conversation_updated': 'Conversation Updated',
        }
    )

    class Meta:
        model = Message
        fields = {
            'sent_at': ['exact', 'gte', 'lte', 'year', 'month', 'day'],
            'sender': ['exact'],
            'conversation': ['exact'],
            'message_body': ['icontains'],
        }

    def filter_by_sender_name(self, queryset, name, value):
        """
        Filter messages by sender's first name or last name.
        """
        return queryset.filter(
            Q(sender__first_name__icontains=value) |
            Q(sender__last_name__icontains=value)
        )

    def filter_conversations_with_user(self, queryset, name, value):
        """
        Filter messages from conversations that include a specific user.
        """
        return queryset.filter(
            conversation__participants__user_id=value
        ).distinct()

    def filter_conversations_with_user_email(self, queryset, name, value):
        """
        Filter messages from conversations that include a user with specific email.
        """
        return queryset.filter(
            conversation__participants__email__icontains=value
        ).distinct()


class ConversationFilter(django_filters.FilterSet):
    """
    Filter class for Conversation model to retrieve conversations with specific users.
    """
    
    # Date filtering
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Participant filtering
    participant_id = django_filters.UUIDFilter(field_name='participants__user_id')
    participant_email = django_filters.CharFilter(field_name='participants__email', lookup_expr='icontains')
    participant_name = django_filters.CharFilter(method='filter_by_participant_name')
    
    # Conversation size filtering
    min_participants = django_filters.NumberFilter(method='filter_min_participants')
    max_participants = django_filters.NumberFilter(method='filter_max_participants')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
        ),
        field_labels={
            'created_at': 'Date Created',
            'updated_at': 'Last Updated',
        }
    )

    class Meta:
        model = Conversation
        fields = {
            'created_at': ['exact', 'gte', 'lte'],
            'updated_at': ['exact', 'gte', 'lte'],
            'participants': ['exact'],
        }

    def filter_by_participant_name(self, queryset, name, value):
        """
        Filter conversations by participant's first name or last name.
        """
        return queryset.filter(
            Q(participants__first_name__icontains=value) |
            Q(participants__last_name__icontains=value)
        ).distinct()

    def filter_min_participants(self, queryset, name, value):
        """
        Filter conversations with at least the specified number of participants.
        """
        return queryset.annotate(
            participant_count=django_filters.Count('participants')
        ).filter(participant_count__gte=value)

    def filter_max_participants(self, queryset, name, value):
        """
        Filter conversations with at most the specified number of participants.
        """
        return queryset.annotate(
            participant_count=django_filters.Count('participants')
        ).filter(participant_count__lte=value)


class UserFilter(django_filters.FilterSet):
    """
    Filter class for User model.
    """
    
    # Name filtering
    name = django_filters.CharFilter(method='filter_by_name')
    first_name = django_filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    
    # Email filtering
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    
    # Date filtering
    joined_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    joined_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Status filtering
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('first_name', 'first_name'),
            ('last_name', 'last_name'),
            ('email', 'email'),
            ('created_at', 'created_at'),
        ),
        field_labels={
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'created_at': 'Date Joined',
        }
    )

    class Meta:
        model = User
        fields = {
            'email': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'is_active': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
        }

    def filter_by_name(self, queryset, name, value):
        """
        Filter users by first name or last name.
        """
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        )