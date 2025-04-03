from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import InternshipSerializer, ApplicationSerializer, InternSerializer,  MentorProfileSerializer , MentorApplicationSerializer, MentorProfileSerializer, TaskSerializer
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from .models import Internship, Application, Intern,  MentorApplication, MentorProfile , Mentor , Task
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from django.db import transaction
from django.core.cache import cache
from django.core.mail import send_mail
import logging
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.hashers import make_password
from rest_framework import viewsets, permissions

from rest_framework.exceptions import PermissionDenied
from django.conf import settings

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_internship_id(request):
    """
    Fetch the internship ID for the logged-in intern.
    """
    user = request.user
    
    try:
        internship_application = Application.objects.get(user=user)
        return Response({"internship_id": internship_application.internship.id})
    except Application.DoesNotExist:
        return Response({"error": "No internship found for this user"}, status=404)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_permissions(self):
        """
        Define permissions: 
        - Mentors can create, update, and delete tasks.
        - Interns can only view tasks.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]  # Interns can view tasks

    def get_queryset(self):
        """
        Fetch tasks, optionally filtered by internship_id.
        """
        queryset = Task.objects.all()
        internship_id = self.request.query_params.get('internship_id')

        if internship_id:
            queryset = queryset.filter(internship=internship_id)

        return queryset
    def perform_create(self, serializer):
        """
        Ensure only the mentor assigned to the internship can create tasks.
        """
        user = self.request.user
        if not hasattr(user, 'mentor_profile'):
            raise PermissionDenied("Only mentors can create tasks.")

        serializer.save(mentor=user.mentor_profile)

    def perform_update(self, serializer):
        """
        Ensure only the assigned mentor can update a task.
        """
        user = self.request.user
        task = self.get_object()

        if task.mentor != user.mentor_profile:
            raise PermissionDenied("You can only update your assigned tasks.")

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """
        Ensure only the assigned mentor can delete a task.
        """
        task = self.get_object()
        user = self.request.user

        if task.mentor != user.mentor_profile:
            raise PermissionDenied("You can only delete your assigned tasks.")

        return super().destroy(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mentor_id(request):
    """Fetch mentor profile ID for the logged-in user."""
    try:
        mentor = MentorProfile.objects.get(user=request.user)
        return Response({"mentor_id": mentor.id})
    except MentorProfile.DoesNotExist:
        return Response({"error": "Mentor profile not found"}, status=404)

# mentor:
class MentorProfileCreateView(generics.CreateAPIView):
    serializer_class = MentorProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure the user does not already have a mentor profile
        user = self.request.user
        if MentorProfile.objects.filter(user=user).exists():
            return Response({"error": "You already have a mentor profile."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the mentor profile
        mentor_profile = serializer.save(user=user)

        # Automatically create a mentor application with status 'pending'
        MentorApplication.objects.create(user=user, internship=mentor_profile.internship)

        return Response({"message": "Mentor profile created successfully and sent for approval."}, status=status.HTTP_201_CREATED)


class MentorApplicationListView(generics.ListAPIView):
    serializer_class = MentorApplicationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return MentorApplication.objects.filter(status="pending")


class MentorApplicationUpdateView(generics.UpdateAPIView):
    serializer_class = MentorApplicationSerializer
    permission_classes = [IsAdminUser]
    queryset = MentorApplication.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get("status", "").lower()

        if new_status not in ["approved", "rejected"]:
            return Response({"error": "Invalid status. Choose 'approved' or 'rejected'."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the application status
        instance.status = new_status
        instance.save()

        if new_status == "approved":
            # Update user role to mentor
            user = instance.user
            user.role = "mentor"
            user.set_password(f"mentor{user.name}123")
            user.save()

            Mentor.objects.get_or_create(user=user)

            # Send email notification
            send_mail(
                subject="Mentor Application Approved",
                message=f"Congratulations {user.name}, your application for a mentor role has been approved! Your new login password is: mentor{user.name}123",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        return Response({"message": f"Mentor application {new_status} successfully."}, status=status.HTTP_200_OK)




# class AdminMentorApplicationViewSet(viewsets.ViewSet):
#     permission_classes = [IsAdminUser]

#     @action(detail=True, methods=['post'])
#     def approve(self, request, pk=None):
#         """
#         Admin approves mentor application
#         - Changes status to 'approved'
#         - Assigns role to 'mentor'
#         - Sends email with password
#         """
#         try:
#             application = MentorApplication.objects.get(pk=pk)
            
#             if application.status != 'pending':
#                 return Response({'error': 'Application is already processed.'}, status=status.HTTP_400_BAD_REQUEST)

#             with transaction.atomic():
#                 # ✅ Approve application
#                 application.status = 'approved'
#                 application.save()

#                 # ✅ Trigger signal for role update and email notification
#                 application.save()

#                 return Response({'message': 'Mentor application approved and role updated.'}, status=status.HTTP_200_OK)

#         except MentorApplication.DoesNotExist:
#             return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

#     @action(detail=True, methods=['post'])
#     def reject(self, request, pk=None):
#         """
#         Admin rejects mentor application
#         - Changes status to 'rejected'
#         - Keeps user role as 'user'
#         """
#         try:
#             application = MentorApplication.objects.get(pk=pk)
            
#             if application.status != 'pending':
#                 return Response({'error': 'Application is already processed.'}, status=status.HTTP_400_BAD_REQUEST)

#             # ✅ Reject application
#             application.status = 'rejected'
#             application.save()

#             # ✅ Set role back to 'user'
#             application.user.role = 'user'
#             application.user.save()

#             return Response({'message': 'Mentor application rejected.'}, status=status.HTTP_200_OK)

#         except MentorApplication.DoesNotExist:
#             return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)


# internship/views.py
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, IsAdminUser
# from django.db import transaction

# from .models import MentorApplication, MentorProfile, Internship
# from users.models import CustomUser
# from .serializers import 


# ✅ Mentor Application ViewSet (for applying as mentor)
# class MentorApplicationViewSet(viewsets.ModelViewSet):
#     queryset = MentorApplication.objects.all()
#     serializer_class = MentorApplicationSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         """Filter applications by current user (non-admin)"""
#         if self.request.user.is_superuser:
#             return MentorApplication.objects.all()
#         return MentorApplication.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         """Assign current user to the application"""
#         serializer.save(user=self.request.user)


# class MentorApplicationViewSet(viewsets.ModelViewSet):
#     queryset = MentorApplication.objects.all()
#     serializer_class = MentorApplicationSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.is_superuser:
#             return MentorApplication.objects.all()
#         return MentorApplication.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         """Create mentor application with the internship ID and the user."""
#         serializer.save(user=self.request.user)


# class AdminMentorApplicationViewSet(viewsets.ViewSet):
#     permission_classes = [IsAdminUser]

#     @action(detail=True, methods=['post'])
#     def approve(self, request, pk=None):
#         """Admin approves mentor application and sends email"""
#         try:
#             application = MentorApplication.objects.get(pk=pk)
            
#             if application.status != 'pending':
#                 return Response({'error': 'Application is already processed.'}, status=status.HTTP_400_BAD_REQUEST)

#             with transaction.atomic():
#                 application.status = 'approved'
#                 application.save()

#                 # Update the user's role to 'mentor'
#                 user = application.user
#                 user.role = 'mentor'
#                 user.save()

#                 # Create the mentor profile if not already created
#                 MentorProfile.objects.get_or_create(
#                     user=user,
#                     internship=application.internship,
#                     defaults={'status': 'approved'}
#                 )

#                 # Send approval email with the password
#                 password = f"mentor+{user.name}_123"
#                 send_mail(
#                     subject='Mentor Application Approved',
#                     message=(
#                         f"Hello {user.name},\n\n"
#                         f"Your mentor application for the internship '{application.internship.title}' has been approved.\n"
#                         f"Your login credentials:\n"
#                         f"Password: {password}\n"
#                         "Please log in to update your profile and start mentoring.\n\n"
#                         "Best regards,\nThe Xpora Team"
#                     ),
#                     from_email=settings.DEFAULT_FROM_EMAIL,
#                     recipient_list=[user.email],
#                     fail_silently=False,
#                 )

#                 return Response({'message': 'Mentor application approved and email sent.'}, status=status.HTTP_200_OK)

#         except MentorApplication.DoesNotExist:
#             return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

#     @action(detail=True, methods=['post'])
#     def reject(self, request, pk=None):
#         """Admin rejects mentor application"""
#         try:
#             application = MentorApplication.objects.get(pk=pk)
            
#             if application.status != 'pending':
#                 return Response({'error': 'Application is already processed.'}, status=status.HTTP_400_BAD_REQUEST)

#             application.status = 'rejected'
#             application.save()

#             return Response({'message': 'Mentor application rejected.'}, status=status.HTTP_200_OK)

#         except MentorApplication.DoesNotExist:
#             return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)





# # ✅ Mentor Profile ViewSet (for creating profiles after approval)
# class MentorProfileViewSet(viewsets.ModelViewSet):
#     queryset = MentorProfile.objects.all()
#     serializer_class = MentorProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         """Filter profiles by current user (non-admin)"""
#         if self.request.user.is_superuser:
#             return MentorProfile.objects.all()
#         return MentorProfile.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         """Create profile for current user with internship ID"""
#         serializer.save(user=self.request.user)



# # ✅ Mentor ViewSet
# class MentorViewSet(viewsets.ModelViewSet):
#     queryset = Mentor.objects.all()
#     serializer_class = MentorSerializer

#     @action(detail=False, methods=['post'])
#     def create_mentor(self, request):
#         """Creates a Mentor with custom password format."""
#         name = request.data.get('name')
#         email = request.data.get('email')
#         expertise = request.data.get('expertise')

#         if not (name and email and expertise):
#             return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

#         if CustomUser.objects.filter(email=email).exists():
#             return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

#         # ✅ Generate custom password
#         password = f"mentor{name.lower()}123"
#         hashed_password = make_password(password)

#         # ✅ Create User and Mentor
#         user = CustomUser.objects.create(
#             name=name,
#             email=email,
#             role='mentor',
#             password=hashed_password
#         )

#         Mentor.objects.create(user=user, expertise=expertise)

#         # ✅ Send Email
#         send_mail(
#             subject='Welcome to Xpora - Mentor Account Created',
#             message=(
#                 f"Hello {name},\n\n"
#                 f"Your mentor account has been created.\n"
#                 f"Login details:\n"
#                 f"📧 Email: {email}\n"
#                 f"🔑 Password: {password}\n\n"
#                 "Please log in and update your profile."
#             ),
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[email],
#             fail_silently=False,
#         )

#         return Response({"message": "Mentor created and email sent successfully"}, status=status.HTTP_201_CREATED)


# # ✅ Mentor Profile Creation View (After Login)
# class MentorProfileCreateView(generics.CreateAPIView):
#     """
#     Allows normal users to create a mentor profile.
#     """
#     queryset = MentorProfile.objects.all()
#     serializer_class = MentorProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         """Create Mentor Profile"""

#         # ✅ Ensure only normal users can create a mentor profile
#         user = request.user

#         if user.role not in ['user', 'intern']:
#             return Response(
#                 {'error': 'Only normal users and interns can create a mentor profile'},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # ✅ Check if the user already has a mentor profile
#         if MentorProfile.objects.filter(user=user).exists():
#             return Response({'error': 'Profile already exists'}, status=status.HTTP_400_BAD_REQUEST)

#         # ✅ Extract data
#         resume = request.FILES.get('resume')
#         expertise = request.data.get('expertise')
#         bio = request.data.get('bio')
#         experience = request.data.get('experience')

#         if not (expertise and bio and experience):
#             return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # ✅ Create the profile and associate it with the user
#             profile = MentorProfile.objects.create(
#                 user=user,
#                 expertise=expertise,
#                 bio=bio,
#                 experience=experience,
#                 resume=resume
#             )
#             profile.save()

#             return Response(
#                 {'message': 'Profile created successfully and sent for approval', 'profile_id': profile.id},
#                 status=status.HTTP_201_CREATED
#             )

#         except ValidationError as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


# class MentorProfileViewSet(viewsets.ModelViewSet):
#     queryset = MentorProfile.objects.all()
#     serializer_class = MentorProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def list(self, request, *args, **kwargs):
#         cache_key = 'mentor_profiles'
#         profiles = cache.get(cache_key)

#         if not profiles:
#             profiles = list(MentorProfile.objects.all())
#             cache.set(cache_key, profiles, timeout=3600)  # Cache for 1 hour

#         serializer = self.get_serializer(profiles, many=True)
#         return Response(serializer.data)

#     def perform_create(self, serializer):
#         """Prevent duplicate mentor profiles"""
#         user = self.request.user

#         # ✅ Check if profile already exists
#         if MentorProfile.objects.filter(user=user).exists():
#             raise ValidationError({"error": "Mentor profile already exists."})  # ✅ Use the correct exception

#         # ✅ Create profile only if it doesn't exist
#         serializer.save(user=user)

#     @action(detail=True, methods=['post'])
#     def approve_profile(self, request, pk=None):
#         """Admin approves the mentor profile"""
#         profile = self.get_object()

#         if profile.status != 'pending':
#             return Response({"error": "Profile already reviewed"}, status=status.HTTP_400_BAD_REQUEST)

#         profile.status = 'approved'
#         profile.save()

#         user = profile.user

#         if user.role == 'user':
#             user.role = 'mentor'

#             new_password = f"mentor{user.name.lower()}123"
#             user.set_password(new_password)
#             user.save()

#             Mentor.objects.get_or_create(user=user, expertise=profile.expertise)

#             send_mail(
#                 'Mentor Profile Approved',
#                 f"""
#                 Hello {user.name},

#                 🎉 Your mentor profile has been approved!

#                 ✅ Your new login credentials:
#                 📧 Email: {user.email}
#                 🔑 Password: {new_password}

#                 Please log in and update your password after first login.

#                 Regards,  
#                 🚀 Xpora Team
#                 """,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 fail_silently=False
#             )

#             return Response(
#                 {
#                     "message": "Profile approved, role upgraded to mentor, and email sent",
#                     "new_password": new_password  # ✅ For testing (remove in production)
#                 },
#                 status=status.HTTP_200_OK
#             )
#         else:
#             return Response(
#                 {"error": "User is already a mentor"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#     @action(detail=True, methods=['post'])
#     def reject_profile(self, request, pk=None):
#         """Admin rejects the mentor profile"""
#         profile = self.get_object()

#         if profile.status != 'pending':
#             return Response({"error": "Profile already reviewed"}, status=status.HTTP_400_BAD_REQUEST)

#         profile.status = 'rejected'
#         profile.save()

#         send_mail(
#             'Mentor Profile Rejected',
#             f"""
#             Hello {profile.user.name},

#             ❌ Unfortunately, your mentor profile has been rejected.
#             You can reapply or contact the admin for more details.

#             Regards,  
#             🚀 Xpora Team
#             """,
#             settings.DEFAULT_FROM_EMAIL,
#             [profile.user.email],
#             fail_silently=False
#         )

#         return Response({"message": "Profile rejected and email sent"}, status=status.HTTP_200_OK)


# # ✅ Admin Assigns Mentor to Internship
# @api_view(['POST'])
# def assign_mentor_to_internship(request, internship_id, mentor_id):
#     """Assign an approved mentor to an internship"""
#     internship = get_object_or_404(Internship, id=internship_id)
#     mentor = get_object_or_404(Mentor, id=mentor_id)

#     if not mentor.user.mentor_profile.status == 'approved':
#         return Response(
#             {"error": "Only approved mentors can be assigned"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     internship.mentor = mentor
#     internship.save()

#     return Response({
#         "message": f"Mentor {mentor.user.name} assigned to {internship.title}"
#     }, status=status.HTTP_200_OK)


# def get_mentors(request):
#     mentors = Mentor.objects.select_related('user').all()
    
#     data = [
#         {
#             "id": mentor.id,
#             "user": {
#                 "id": mentor.user.id,
#                 "name": mentor.user.name,
#                 "email": mentor.user.email
#             },
#             "expertise": mentor.expertise
#         }
#         for mentor in mentors
#     ]

#     return JsonResponse(data, safe=False)


# # ✅ Remove a mentor
# @csrf_exempt
# def delete_mentor(request, mentor_id):
#     if request.method == "DELETE":
#         try:
#             mentor = Mentor.objects.get(id=mentor_id)
#             mentor.delete()
#             return JsonResponse({"message": "Mentor removed successfully"}, status=200)
#         except ObjectDoesNotExist:
#             return JsonResponse({"error": "Mentor not found"}, status=404)

#     return JsonResponse({"error": "Invalid request method"}, status=400)

class ApplicationViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Internship Applications
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Create an application only if the user has a completed profile
        """
        user = request.user

        if not user.is_profile_completed:
            return Response({'error': 'Complete your profile before applying'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    # ✅ Approve application, create intern, and send email
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Approve an application, update the user's role, create an Intern entry, and send email.
        """
        application = self.get_object()
        user = application.user  # ✅ Get the user directly

        # ✅ Generate new password: username + "123"
        new_password = f"{user.name}123"

        try:
            with transaction.atomic():
                # ✅ Approve the application
                application.status = 'approved'
                application.save()

                # ✅ Update user's role
                if user.role != 'intern':
                    user.role = 'intern'

                # ✅ Properly hash the password before saving
                user.set_password(new_password)
                user.save()

                # ✅ Clear cache
                cache.delete(f"user_{user.id}")
                cache.clear()

                # ✅ Create or update Intern entry
                intern, created = Intern.objects.get_or_create(
                    user=user,
                    internship=application.internship,
                    defaults={'is_approved': True}
                )

                if not created:
                    intern.is_approved = True
                    intern.save()

                # ✅ Send email with new credentials
                subject = "🎉 Internship Application Approved"
                message = (
                    f"Hello {user.name},\n\n"
                    "Your internship application has been approved!\n\n"
                    "You are now an intern on Xpora.\n"
                    "Please re-login using the following credentials:\n\n"
                    f"📧 Email: {user.email}\n"
                    f"🔑 New Password: {new_password}\n\n"
                    "Thank you and welcome aboard!\n"
                    "🚀 Xpora Team"
                )

                logger.info(f"Sending email to: {user.email}")

                send_mail(
                    subject,
                    message,
                    'your_email@gmail.com',  # ✅ Your sender email
                    [user.email],
                    fail_silently=False,
                )

                logger.info(f"Email sent to {user.email} with password {new_password}")

        except Exception as e:
            logger.error(f"Error approving application: {str(e)}")
            return Response({
                'error': 'Failed to approve application',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ✅ Reload the user to reflect updated role immediately
        user.refresh_from_db()

        return Response({
            'message': 'Application approved, intern added. Email sent.',
            'intern_id': intern.id,
            'user_role': user.role  # ✅ Confirm updated role
        }, status=status.HTTP_200_OK)

    # ✅ New Reject Action
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """
        Reject an application and send an email notification to the user.
        """
        application = self.get_object()
        user = application.user

        # ✅ Check if already rejected
        if application.status == 'rejected':
            return Response({
                'message': 'Application already rejected.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # ✅ Update application status
                application.status = 'rejected'
                application.save()

                # ✅ Clear cache
                cache.delete(f"user_{user.id}")
                cache.clear()

                # ✅ Send rejection email
                subject = "❌ Internship Application Rejected"
                message = (
                    f"Hello {user.name},\n\n"
                    "We regret to inform you that your internship application "
                    "on Xpora has been rejected.\n\n"
                    "Please feel free to apply for other opportunities in the future.\n\n"
                    "Best Regards,\n"
                    "🚀 Xpora Team"
                )

                send_mail(
                    subject,
                    message,
                    'your_email@gmail.com',  # ✅ Your sender email
                    [user.email],
                    fail_silently=False,
                )

                logger.info(f"Email sent to {user.email} for rejection.")

        except Exception as e:
            logger.error(f"Error rejecting application: {str(e)}")
            return Response({
                'error': 'Failed to reject application',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'message': 'Application rejected, email sent.',
            'user_email': user.email
        }, status=status.HTTP_200_OK)

class InternViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Interns
    """
    serializer_class = InternSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Fetch only approved interns with related user and internship details
        """
        return Intern.objects.filter(is_approved=True).select_related('user', 'internship')

# ✅ Apply for Internship API
@api_view(['POST'])
def apply_for_internship(request, internship_id):
    """
    Apply for an internship only if the profile is completed
    """
    user = request.user

    if not user.is_profile_completed:
        return Response({"error": "Please complete your profile before applying."}, status=400)

    try:
        internship = Internship.objects.get(id=internship_id)

        if Application.objects.filter(user=user, internship=internship).exists():
            return Response({"error": "You have already applied for this internship."}, status=400)

        application = Application.objects.create(user=user, internship=internship)
        return Response({"message": "Application submitted successfully!"}, status=201)

    except Internship.DoesNotExist:
        return Response({"error": "Internship not found."}, status=404)

# ✅ Retrieve all applications by the logged-in user
@api_view(['GET'])
def my_applications(request):
    """
    Retrieve all internship applications by the logged-in user
    """
    user = request.user
    applications = Application.objects.filter(user=user)

    data = [
        {
            "internship": app.internship.title,
            "status": app.status,
            "applied_at": app.applied_at.strftime("%Y-%m-%d %H:%M")
        }
        for app in applications
    ]

    return Response(data, status=status.HTTP_200_OK)

# ✅ Internship Detail View
class InternshipDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]  # Public access (no login required)
    queryset = Internship.objects.all()
    serializer_class = InternshipSerializer

# ✅ Internship List View
class InternshipListView(APIView):
    permission_classes = [AllowAny]  # Public access (no login required)

    def get(self, request):
        internships = Internship.objects.all()
        serializer = InternshipSerializer(internships, many=True)
        return Response(serializer.data)