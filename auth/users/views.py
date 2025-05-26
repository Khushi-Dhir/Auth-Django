from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import generics
from django.utils.http import urlsafe_base64_encode
from djoser.views import UserViewSet
from rest_framework import status
from .serializers import UserProfileSerializer , CustomUserDetailSerializer ,UserCreateSerializer
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile , CustomUser
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import action
from rest_framework import viewsets

class UserViewSet(viewsets.ModelViewSet):  
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'is_profile_completed': user.is_profile_completed
        })


@api_view(['GET'])
@renderer_classes([JSONRenderer])  # ✅ Set renderer explicitly
def user_role(request):
    user = request.user
    if not user.is_authenticated:
        return Response({'error': 'Unauthorized'}, status=401, content_type='application/json')

    return Response({
        'role': user.role,
        'uid': user.id  # ✅ Return raw integer ID
    }, content_type='application/json')

class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CustomUserDetailSerializer
        return UserCreateSerializer  # or whatever your default is

    def activation(self, request, *args, **kwargs):
        print("✅ Activation request received")
        return super().activation(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = CustomUserDetailSerializer(queryset, many=True)
        print("✅ List of users:", serializer.data)  # Debugging line
        return Response(serializer.data)



class ProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.serializer_class(profile)
        return Response({
            "profile": serializer.data,
            "is_profile_completed": profile.is_complete()
        }, status=status.HTTP_200_OK)


    def post(self, request, *args, **kwargs):
        user = request.user
        if UserProfile.objects.filter(user=user).exists():
            return Response({"message": "Profile already exists. Use PUT to update."}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            user.is_profile_completed = True
            user.save()
            return Response({"message": "Profile created", "profile": serializer.data}, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.serializer_class(
            profile,
            data=request.data,
            partial=True,
            context={"request": request}  # 👈 This adds the request to context
        )
        if serializer.is_valid():
            serializer.save()
            # Check if profile is now complete
            profile.refresh_from_db()  # Ensure latest saved values are loaded
            request.user.is_profile_completed = profile.is_complete()
            request.user.save()
            return Response({"message": "Profile updated", "profile": serializer.data}, status=200)
        return Response(serializer.errors, status=400)
