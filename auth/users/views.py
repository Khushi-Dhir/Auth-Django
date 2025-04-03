from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import generics
from django.utils.http import urlsafe_base64_encode
from djoser.views import UserViewSet
from rest_framework import status
from .serializers import ProfileSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Profile
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer



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
    def activation(self, request, *args, **kwargs):
        print("✅ Activation request received")  # Debugging
        return super().activation(request, *args, **kwargs)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve, Create, and Update Profile
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Fetch or create the profile associated with the authenticated user.
        """
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request, *args, **kwargs):
        """
        Retrieve the profile
        """
        profile = self.get_object()
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Create a new profile if it doesn't exist
        """
        user = request.user

        # Check if the profile already exists
        if Profile.objects.filter(user=user).exists():
            return Response({
                "message": "Profile already exists. Use PUT to update."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=user)
            user.is_profile_completed = True
            user.save()
            return Response({
                "message": "Profile created successfully",
                "profile": serializer.data,
                "is_profile_completed": user.is_profile_completed
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        Update the existing profile
        """
        profile = self.get_object()
        serializer = ProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            user = request.user
            user.is_profile_completed = True
            user.save()
            return Response({
                "message": "Profile updated successfully",
                "profile": serializer.data,
                "is_profile_completed": user.is_profile_completed
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
