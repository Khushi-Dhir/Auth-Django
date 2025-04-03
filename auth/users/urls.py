from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import user_role,  ProfileDetailView, CustomUserViewSet

# Register Custom User ViewSet for activation
router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),  # This will handle user activation
    path('role/', user_role , name='user_role'),
    path('profile/', ProfileDetailView.as_view(), name='profile-detail'),

    # Include Djoser's authentication URLs
    path('auth/', include('djoser.urls')),  
    path('auth/', include('djoser.urls.authtoken')),  
]
