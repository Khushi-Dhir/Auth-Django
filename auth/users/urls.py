from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import user_role, ProfileDetailView, CustomUserViewSet,UserViewSet

# Register Custom User ViewSet for activation
router = DefaultRouter()
router.register(r'users-details', CustomUserViewSet, basename='users')
router.register(r'user', UserViewSet, basename='user')  

urlpatterns = [
    path('', include(router.urls)),  # Handles activation from CustomUserViewSet
    path('role/', user_role, name='user_role'),
    path('profile/', ProfileDetailView.as_view(), name='profile-detail'),

    # Include Djoser's authentication endpoints
    path('auth/', include('djoser.urls')),  
    path('auth/', include('djoser.urls.authtoken')),  
]
