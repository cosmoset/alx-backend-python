"""messaging_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    """
    API root endpoint with available endpoints.
    """
    return JsonResponse({
        'message': 'Welcome to Messaging App API',
        'version': '1.0',
        'endpoints': {
            'auth': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'token': '/api/auth/token/',
                'token_refresh': '/api/auth/token/refresh/',
                'token_verify': '/api/auth/token/verify/',
                'profile': '/api/auth/profile/',
                'update_profile': '/api/auth/profile/update/',
                'change_password': '/api/auth/profile/change-password/',
            },
            'api': {
                'users': '/api/users/',
                'conversations': '/api/conversations/',
                'messages': '/api/messages/',
            },
            'admin': '/admin/',
            'api_auth': '/api-auth/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chats.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', api_root, name='api_root'),
]