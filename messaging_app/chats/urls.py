from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers as nested_routers
from .views import ConversationViewSet, MessageViewSet, UserViewSet
from .auth import (
    register_user,
    login_user,
    logout_user,
    user_profile,
    update_profile,
    change_password,
    CustomTokenObtainPairView
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

# Create a router and register our viewsets
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'users', UserViewSet, basename='user')

# Create nested router for messages within conversations
conversations_router = nested_routers.NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', MessageViewSet, basename='conversation-messages')

# Authentication URLs
auth_patterns = [
    # JWT Token endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair_alt'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Custom auth endpoints
    path('register/', register_user, name='register'),
    path('login-custom/', login_user, name='login_custom'),
    path('logout/', logout_user, name='logout'),
    
    # User profile endpoints
    path('profile/', user_profile, name='user_profile'),
    path('profile/update/', update_profile, name='update_profile'),
    path('profile/change-password/', change_password, name='change_password'),
]

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Authentication routes
    path('auth/', include(auth_patterns)),
    
    # API routes
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
]