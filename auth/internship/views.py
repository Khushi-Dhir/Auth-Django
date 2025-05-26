from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import (
    Internship, Application, Intern, Task, MentorAssignment, PaymentProof, TaskStatus,OfferLetterTemplate, ClientProfile ,Skill ,Certificate, InternshipSchedule 
)
from rest_framework.decorators import action
from rest_framework import serializers
from .serializers import (
    InternshipSerializer, ApplicationSerializer, InternSerializer, ClientProfileSerializer, CertificateSerializer,
    TaskSerializer, MentorAssignmentSerializer, PaymentProofSerializer ,SkillSerializer, OfferLetterTemplateSerializer,InternshipScheduleSerializer
)
from users.serializers import CustomUserDetailSerializer
from django.core.exceptions import ValidationError
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from users.models import CustomUser
from rest_framework.generics import ListAPIView
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated , AllowAny, IsAdminUser
from django.db import models
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from xhtml2pdf import pisa
from reportlab.lib.pagesizes import landscape, A4
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from internship.models import Application, OfferLetterTemplate
from users.models import CustomUser
from django.http import Http404
from io import BytesIO
from internship.models import Certificate
from django.core.files.storage import FileSystemStorage
fs = FileSystemStorage(location='media/certificates')
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from users.models import CustomUser
from internship.models import Internship, MentorAssignment, Application, Task, Certificate, Intern
from internship.serializers import (
    InternshipSerializer, MentorAssignmentSerializer, TaskStatusSerializer,
    ApplicationSerializer, TaskSerializer, CertificateSerializer, InternSerializer
)
from users.serializers import CustomUserDetailSerializer
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def approve_certificate(request, certificate_id):
    user = request.user

    if user.role != 'mentor':
        return Response({'detail': 'Only mentors can approve certificates.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        certificate = Certificate.objects.select_related('internship').get(certificate_id=certificate_id)
    except Certificate.DoesNotExist:
        return Response({'detail': 'Certificate not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if mentor is assigned to this internship
    if not MentorAssignment.objects.filter(internship=certificate.internship, user=user).exists():
        return Response({'detail': 'You are not assigned as a mentor for this internship.'}, status=status.HTTP_403_FORBIDDEN)

    certificate.is_approved_by_mentor = True
    certificate.save()

    return Response({'detail': 'Certificate approved successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mentor_certificates(request):
    user = request.user

    if user.role != 'mentor':
        return Response({'detail': 'Only mentors can view certificates.'}, status=status.HTTP_403_FORBIDDEN)

    # Get internship IDs assigned to this mentor
    assigned_internship_ids = MentorAssignment.objects.filter(user=user).values_list('internship_id', flat=True)

    # Get certificates related to those internships
    certificates = Certificate.objects.filter(internship__id__in=assigned_internship_ids)

    data = [
        {
            'certificate_id': cert.certificate_id,
            'intern_name': cert.user.name,      # ✅ Extract the name
            'intern_email': cert.user.email,
            'intern_id': cert.user.id,
            'internship_title': cert.internship.title,
        }
        for cert in certificates
    ]

    return Response(data, status=status.HTTP_200_OK)


class MentorTaskSetupView(generics.CreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        assignment = MentorAssignment.objects.filter(user=user, status='approved').first()
        if not assignment:
            raise serializers.ValidationError("You are not an assigned mentor.")

        # Automatically set the internship and mentor
        serializer.save(mentor=assignment, internship=assignment.internship)

class InternTaskSubmissionView(generics.CreateAPIView):
    serializer_class = TaskStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        task = serializer.validated_data.get('task')

        if not task:
            raise serializers.ValidationError("Task ID is required.")

        # Get internship from task
        internship = task.internship

        # Find the intern by user + internship
        try:
            intern = Intern.objects.get(user=user, internship=internship)
        except Intern.DoesNotExist:
            raise serializers.ValidationError("You are not registered for this internship.")
        except Intern.MultipleObjectsReturned:
            intern = Intern.objects.filter(user=user, internship=internship).first()

        # Save the submission
        serializer.save(intern=intern)

class MentorScheduleListView(generics.ListAPIView):
    serializer_class = InternshipScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get internships where this user is a mentor
        mentor_internships = MentorAssignment.objects.filter(
            user=self.request.user
        ).values_list('internship_id', flat=True)
        
        # Return schedules for those internships
        return InternshipSchedule.objects.filter(internship_id__in=mentor_internships)


class MentorTaskUpdateView(generics.UpdateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.all()
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user

        if task.mentor.user != user:
            raise serializers.ValidationError("You cannot update this task.")

        data = {
            'title': request.data.get('title'),
            'due_date': request.data.get('due_date'),
        }

        serializer = self.get_serializer(task, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class MentorTaskReviewView(generics.UpdateAPIView):
    serializer_class = TaskStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TaskStatus.objects.all()
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        task_status = self.get_object()
        user = request.user

        # Confirm mentor is assigned to the task
        if task_status.task.mentor.user != user:
            raise serializers.ValidationError("You cannot review this task.")

        # Allow mentor to update review and completion status
        data = {
            'mentor_reviewed': request.data.get('mentor_reviewed', task_status.mentor_reviewed),
            'marked_completed': request.data.get('marked_completed', task_status.marked_completed),
        }

        serializer = self.get_serializer(task_status, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class TaskStatusListView(generics.ListAPIView):
    serializer_class = TaskStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TaskStatus.objects.filter(intern__user=user)


    

class MentorTaskStatusListView(generics.ListAPIView):
    serializer_class = TaskStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        assignment = MentorAssignment.objects.filter(user=user, status='approved').first()
        
        if not assignment:
            raise serializers.ValidationError("You are not an assigned mentor.")
        
        return TaskStatus.objects.filter(task__mentor=assignment)



class GenerateScheduleView(generics.CreateAPIView):
    serializer_class = InternshipScheduleSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, internship_id):
        try:
            internship = Internship.objects.get(id=internship_id)
        except Internship.DoesNotExist:
            return Response({"error": "Internship not found."}, status=status.HTTP_404_NOT_FOUND)

        start_date = internship.start_date
        end_date = internship.end_date
        total_days = (end_date - start_date).days
        total_weeks = total_days // 7

        if total_weeks == 0:
            return Response({"error": "Internship duration too short to create schedule."}, status=400)

        # Clean up existing schedule first
        InternshipSchedule.objects.filter(internship=internship).delete()

        schedules = []
        for week in range(total_weeks):
            week_start = start_date + timedelta(days=week * 7)
            week_end = week_start + timedelta(days=6)

            schedule = InternshipSchedule(
                internship=internship,
                week_number=week + 1,
                title=f"Week {week + 1} Title",
                description=f"Description for week {week + 1} (edit this)",
                start_date=week_start,
                end_date=min(week_end, end_date),
                is_mandatory=True,
            )
            schedules.append(schedule)

        InternshipSchedule.objects.bulk_create(schedules)
        return Response({"message": f"{total_weeks} weeks scheduled successfully."}, status=201)


class ScheduleListView(generics.ListAPIView):
    serializer_class = InternshipScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        internship_id = self.kwargs['internship_id']
        return InternshipSchedule.objects.filter(internship_id=internship_id).order_by('week_number')


class ScheduleUpdateView(generics.UpdateAPIView):
    queryset = InternshipSchedule.objects.all()
    serializer_class = InternshipScheduleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'



class ReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = user.role
        data = {}

        def get_enhanced_internship_data(internships):
            """Returns a list of dicts with enriched internship data."""
            enriched = []
            for internship in internships:
                assigned_mentors = MentorAssignment.objects.filter(internship=internship)
                approved_interns_count = Application.objects.filter(internship=internship, status='approved').count()
                enriched.append({
                    "id": internship.id,
                    "title": internship.title,
                    "description": internship.description,
                    "start_date": internship.start_date,
                    "end_date": internship.end_date,
                    "is_active": internship.is_active,
                    "capacity": internship.capacity,
                    "current_interns": approved_interns_count,
                    "assigned_mentors": MentorAssignmentSerializer(assigned_mentors, many=True).data,
                    "client": {
                        "id": internship.client.user.id,
                        "username": internship.client.user.name,
                        "email": internship.client.user.email
                    }
                })
            return enriched

        if role == 'admin':
            internships = Internship.objects.all()
            all_clients = ClientProfile.objects.select_related('user').all()
            clients_data = []

            for client in all_clients:
                client_internships = Internship.objects.filter(client=client)
                enriched_internships = get_enhanced_internship_data(client_internships)
                clients_data.append({
                    "client_id": client.user.id,
                    "client_name": client.user.name,
                    "client_email": client.user.email,
                    "internships": enriched_internships
                })

            data = {
                "all_users": CustomUserDetailSerializer(CustomUser.objects.all(), many=True).data,
                "all_internships": get_enhanced_internship_data(internships),
                "clients_with_internships": clients_data,
                "all_applications": ApplicationSerializer(Application.objects.all(), many=True).data,
                "interns": InternSerializer(Intern.objects.all(), many=True).data,
                "mentors": CustomUserDetailSerializer(CustomUser.objects.filter(role='mentor'), many=True).data,
            }

        elif role == 'client':
            internships = Internship.objects.filter(client__user=user)
            assignments = MentorAssignment.objects.filter(internship__in=internships)
            approved_applications = Application.objects.filter(internship__in=internships, status='approved')

            data = {
                "my_internships": get_enhanced_internship_data(internships),
                "mentors_added": MentorAssignmentSerializer(assignments, many=True).data,
                "interns_enrolled": ApplicationSerializer(approved_applications, many=True).data,
            }

        elif role == 'mentor':
            assignments = MentorAssignment.objects.filter(user=user)
            assigned_internships = [a.internship for a in assignments]
            tasks = Task.objects.filter(internship__in=assigned_internships)
            pending_certs = Certificate.objects.filter(internship__in=assigned_internships, is_approved_by_mentor=False)

            data = {
                "assigned_internships": get_enhanced_internship_data(assigned_internships),
                "tasks_submitted": TaskSerializer(tasks, many=True).data,
                "pending_certificates": CertificateSerializer(pending_certs, many=True, context={'request': request}).data,
            }

        else:
            return Response({"detail": "Invalid role"}, status=403)

        return Response(data)

class CertificatePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, internship_id):
        internship = get_object_or_404(Internship, id=internship_id)

        # Get or create certificate
        certificate, created = Certificate.objects.get_or_create(
            user=request.user,
            internship=internship,
            defaults={"is_approved_by_mentor": False}
        )

        # Only allow access if it's the user or staff
        if certificate.user != request.user and not request.user.is_staff:
            return Response({"detail": "Not authorized"}, status=403)

        # Require mentor approval
        if not certificate.is_approved_by_mentor:
            return Response({"detail": "Certificate not yet approved by mentor."}, status=403)

        # Gather needed data
        client_profile = internship.client
        client_user = client_profile.user
        client_name = client_user.name
        company_name = client_profile.company_name

        mentor_assignment = MentorAssignment.objects.filter(internship=internship).first()
        mentor_user = mentor_assignment.user if mentor_assignment else None

        # Generate PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)

        # Header
        p.setFont("Helvetica-Bold", 36)
        p.setFillColor(colors.darkblue)
        p.drawCentredString(width / 2, height - 80, "XPORA")

        p.setFont("Helvetica-Bold", 24)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, height - 130, "Certificate of Completion")

        p.setStrokeColor(colors.grey)
        p.line(100, height - 140, width - 100, height - 140)

        # Body
        p.setFont("Helvetica", 16)
        p.drawCentredString(width / 2, height - 190, "This is to certify that")

        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width / 2, height - 230, f"{certificate.user.name}")

        p.setFont("Helvetica", 16)
        p.drawCentredString(width / 2, height - 270, "has successfully completed the internship in")

        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width / 2, height - 310, f"{internship.title}")

        p.setFont("Helvetica", 14)
        p.drawCentredString(width / 2, height - 350, f"at {company_name}")

        p.setFont("Helvetica-Oblique", 12)
        issued_date = certificate.issued_at.date() if certificate.issued_at else timezone.now().date()
        p.drawCentredString(width / 2, height - 390, f"Issued on: {issued_date}")

        # Signatures
        y = 130
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, f"{client_name}")
        p.setFont("Helvetica", 10)
        p.drawString(100, y - 15, "Client")

        if mentor_user:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(width - 250, y, f"{mentor_user.name}")
            p.setFont("Helvetica", 10)
            p.drawString(width - 250, y - 15, "Mentor")

        # Footer
        p.setFont("Helvetica-Oblique", 10)
        p.setFillColor(colors.grey)
        p.drawCentredString(width / 2, 40, "This certificate was generated by Xpora Internship Platform.")

        # Finalize PDF
        p.showPage()
        p.save()
        buffer.seek(0)

        filename = f"Certificate_{internship_id}.pdf"
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{context_dict.get('intern_name', 'offer_letter')}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response


def generate_offer_letter_pdf(request, internship_id):
    try:
        internship = Internship.objects.get(id=internship_id)
        client_profile = internship.client
        client_user = client_profile.user
        company_name = client_profile.company_name

        # Get approved intern (assuming one intern per request or change logic as needed)
        intern_application = internship.applications.filter(status='approved').first()
        intern_user = intern_application.user if intern_application else None

        # Get mentor
        mentor_assignment = MentorAssignment.objects.filter(internship=internship).first()
        mentor_user = mentor_assignment.user if mentor_assignment else None

        # Start the PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Offer_Letter_{internship_id}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        # Set XPORA Heading
        p.setFont("Helvetica-Bold", 28)
        p.setFillColor(colors.darkblue)
        p.drawCentredString(width / 2, height - 80, "XPORA")

        # Reset color and smaller subheading
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, height - 110, "Internship Offer Letter")

        # Company Name
        p.setFont("Helvetica", 12)
        p.drawCentredString(width / 2, height - 140, f"Offered by: {company_name}")

        # Content Block
        y = height - 200
        p.setFont("Helvetica", 12)
        p.drawString(80, y, f"Dear {intern_user.name if intern_user else 'Intern'},")
        y -= 30
        p.drawString(80, y, f"We are delighted to offer you the position of intern for the project:")
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, f"{internship.title}")
        y -= 30
        p.setFont("Helvetica", 12)
        p.drawString(80, y, f"The internship will begin on {internship.start_date} and conclude on {internship.end_date}.")
        y -= 30
        p.drawString(80, y, "Throughout this period, you will be guided by our assigned mentor and team.")
        y -= 20
        p.drawString(80, y, "We trust this experience will contribute greatly to your career development.")

        # Signature Section
        y -= 80
        p.drawString(80, y, "Sincerely,")

        y -= 60
        p.setFont("Helvetica-Bold", 12)
        p.drawString(80, y, f"{client_user.name} ")
        p.setFont("Helvetica", 10)
        p.drawString(80, y - 15, f"Client - {company_name}")

        if mentor_user:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(320, y, f"{mentor_user.name} ")
            p.setFont("Helvetica", 10)
            p.drawString(320, y - 15, "Mentor")

        # Footer
        p.setFont("Helvetica-Oblique", 10)
        p.drawCentredString(width / 2, 50, "This letter was auto-generated by Xpora Internship Platform.")

        p.showPage()
        p.save()
        return response

    except Internship.DoesNotExist:
        return HttpResponse("Internship not found.", status=404)


class OfferLetterPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, internship_id):
        intern = request.user
        try:
            application = Application.objects.get(user=intern, internship__id=internship_id, status='approved')
        except Application.DoesNotExist:
            raise Http404("You are not approved for this internship")

        internship = application.internship
        client_profile = internship.client
        print(f"Client Profile: {client_profile}")
        print(f"Internship: {internship}")

        # Debugging: check if the client profile exists
        if not client_profile:
            raise Http404("Client profile not found for the internship.")

        try:
            template_obj = OfferLetterTemplate.objects.get(client=client_profile)
        except OfferLetterTemplate.DoesNotExist:
            # Debugging: log the client and internship data
            print(f"Offer letter template not found for client {client_profile.id} associated with internship {internship.id}.")
            raise Http404("Offer letter template not found for this client.")

        offer_body = template_obj.generate_full_body(intern.name, internship)
        signature_name = template_obj.signature_name or client_profile.user
        signature_image = template_obj.signature_image.url if template_obj.signature_image else None

        context = {
            "intern_name": intern.name,
            "company_name": client_profile.company_name,
            "body": offer_body,
            "signature_name": signature_name,
            "signature_image": signature_image,
            "date": template_obj.date,
        }

        return render_to_pdf("offerletter_template.html", context)

class SkillListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        skills = Skill.objects.all()
        serializer = SkillSerializer(skills, many=True)
        return Response(serializer.data)


# --------- INTERNSHIP LIST / DETAIL ---------
class LatestInternshipView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        internship = Internship.objects.filter(is_active=True).order_by('-id').first()
        if internship:
            serializer = InternshipSerializer(internship)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "No internships found."}, status=status.HTTP_404_NOT_FOUND)
    
class InternshipListView(generics.ListAPIView):
    queryset = Internship.objects.filter(is_active=True)
    serializer_class = InternshipSerializer
    permission_classes = [permissions.AllowAny]

class CreateClientProfileView(generics.CreateAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return user.client_profile
        except ClientProfile.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        if not profile:
            return Response({"message": "Client profile not found."}, status=404)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        user = request.user

        if hasattr(user, 'client_profile'):
            return Response({"message": "Client profile already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            client_profile = serializer.save(user=user)

            # DO NOT change user role yet
            return Response({
                "message": "Client profile created successfully. Awaiting admin verification.",
                "profile": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        if not profile:
            return Response({"message": "Client profile not found."}, status=404)
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated", "profile": serializer.data})
        return Response(serializer.errors, status=400)

    def delete(self, request, *args, **kwargs):
        profile = self.get_object()

        if not profile:
            return Response({"message": "Client profile not found."}, status=404)

        profile.delete()

        request.user.role = "user"
        request.user.save()

        return Response({"message": "Client profile deleted successfully. User role reverted to 'user'."})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def unverified_clients(request):
    clients = ClientProfile.objects.filter(is_verified=False)
    serializer = ClientProfileSerializer(clients, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def verify_client(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        profile = user.client_profile
    except (CustomUser.DoesNotExist, ClientProfile.DoesNotExist):
        return Response({"message": "User or client profile not found."}, status=status.HTTP_404_NOT_FOUND)

    if profile.is_verified:
        return Response({"message": "Client is already verified."}, status=status.HTTP_400_BAD_REQUEST)

    # Mark as verified
    profile.is_verified = True
    profile.save()

    # Update user role and password
    user.role = "client"
    temp_password = f"client{user.name}123"
    user.set_password(temp_password)
    user.save()

    # Send email to client
    send_mail(
        subject="Xpora Client Verification Approved",
        message=f"Hello {user.name},\n\nYour client account has been approved!\n\nLogin with:\nEmail: {user.email}\nPassword: {temp_password}\n\nYou can now create internships and manage mentors.\n\n- Xpora Team",
        from_email="xpora.internship@gmail.com",
        recipient_list=[user.email],
        fail_silently=False,
    )

    return Response(
        {"message": f"Client '{user.name}' has been verified and their role updated to 'client'."},
        status=status.HTTP_200_OK
    )

class CreateInternshipView(generics.CreateAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        try:
            client_profile = user.client_profile
        except:
            raise ValidationError("Client profile not found. Please complete your company profile first.")

        # Count user's existing internships
        is_first_internship = Internship.objects.filter(client=client_profile).count() == 0

        # Default fee and UPI
        fee = 0 if is_first_internship else 50
        upi_id = "khushidhir54@okicici"

        # Save internship
        internship = serializer.save(
            client=client_profile,
            fee=fee,
            upi_id=upi_id,
            is_active=True  # if you want it auto-approved
        )



class ClientInternshipListView(generics.ListAPIView):
    serializer_class = InternshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            client_profile = user.client_profile
            return Internship.objects.filter(client=client_profile).order_by('-start_date')
        except ClientProfile.DoesNotExist:
            return Internship.objects.none()

class InternshipDetailView(generics.RetrieveAPIView):
    queryset = Internship.objects.all()
    serializer_class = InternshipSerializer
    permission_classes = [permissions.AllowAny]


# --------- INTERN APPLICATION ---------
class MyInternshipView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            intern = Intern.objects.get(user=request.user)
            internship = intern.internship
            serializer = InternshipSerializer(internship)
            return Response(serializer.data)
        except Intern.DoesNotExist:
            return Response({"error": "Intern record not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == 'admin':
            user_id = request.query_params.get('user_id')
            if user_id:
                applications = Application.objects.filter(user__id=user_id)
            else:
                applications = Application.objects.all()
        else:
            applications = Application.objects.filter(user=user)

        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    def post(self, request):
        if request.user.role != 'admin':
            return Response({'detail': 'Not authorized'}, status=403)

        application_id = request.data.get('application_id')

        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return Response({'detail': 'Application not found'}, status=404)

        if not application.is_first_internship:
            return Response({'detail': 'This is not a first internship. Use payment proof flow to approve.'}, status=400)

        # Approve the application
        application.status = 'approved'
        application.save()

        # Create Intern instance
        intern, created = Intern.objects.get_or_create(
            user=application.user,
            internship=application.internship,
            defaults={'is_approved': True}
        )

        if not created:
            intern.is_approved = True
            intern.save()

        return Response({'detail': 'First internship approved by admin successfully.'})


class ApplyToInternshipView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        internship = serializer.validated_data['internship']

        if Application.objects.filter(user=user, internship=internship).exists():
            raise serializers.ValidationError("You've already applied to this internship.")

        # Check if this is user's first ever approved internship
        is_first = not Application.objects.filter(user=user, status='pending').exists()

        # Save the application with `is_first_internship` flag
        serializer.save(user=user, status='pending', is_first_internship=is_first)


# --------- PAYMENT UPLOAD BY INTERN ---------
class UploadPaymentProofView(generics.CreateAPIView):
    serializer_class = PaymentProofSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

class VerifyPaymentProofView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            proof = PaymentProof.objects.get(pk=pk)
            application = proof.application
            internship = application.internship
            client_user = internship.client.user
            intern_user = application.user

            print(f"Client Profile: {client_user}")
            print(f"Intern Profile: {intern_user.email}")
            print(f"Request User: {request.user}")
            print(f"Company Name: {internship.client.company_name}")
            print(f"Intern Email: {intern_user.email}")
            print(f"Email Sender: {settings.DEFAULT_FROM_EMAIL}")

            # Approve the payment
            proof.verified = True
            proof.save()

            # Approve the application
            application.status = 'approved'
            application.save()

            # Create or get the intern
            try:
                intern, created = Intern.objects.get_or_create(
                    user=intern_user,
                    internship=internship,
                    defaults={'is_approved': True}
                )
            except Exception as e:
                print("⚠️ Error while creating Intern object:", str(e))
                return Response({'detail': 'Error creating intern object', 'error': str(e)}, status=500)

            if created:
                print("✅ New Intern object created — signal should trigger.")
            else:
                print("⚠️ Intern already exists — manually triggering signal via save().")
                intern.is_approved = True
                intern.save()

            print("🔍 Request user role:", request.user.role)
            print("🎓 Intern role:", intern_user.role)
            print("📧 Intern email:", intern_user.email)

            return Response({'detail': 'Intern approved and notified via email.'})

        except PaymentProof.DoesNotExist:
            return Response({'detail': 'Payment not found'}, status=404)



class PaymentProofListView(ListAPIView):
    queryset = PaymentProof.objects.all().order_by('-uploaded_at')
    serializer_class = PaymentProofSerializer
    permission_classes = [IsAdminUser]

# --------- MENTOR ASSIGNMENT REQUEST ---------
class MentorAssignmentView(generics.CreateAPIView):
    serializer_class = MentorAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AddMentorByClientView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client = request.user
        if client.role != 'client':
            return Response({'detail': 'Not authorized'}, status=403)

        name = request.data.get('name')
        email = request.data.get('email')
        internship_id = request.data.get('internship_id')

        # ✅ Validate input
        if not name or not email or not internship_id:
            return Response(
                {'detail': 'Name, email, and internship_id are required.'},
                status=400
            )

        client_profile = get_object_or_404(ClientProfile, user=client)
        internship = get_object_or_404(Internship, id=internship_id, client=client_profile)

        user, created = CustomUser.objects.get_or_create(email=email, defaults={
            'name': name,
            'role': 'mentor',
            'is_active': True
        })

        if created:
            password = f"mentor{name.lower()}123"
            user.set_password(password)
            user.save()

            send_mail(
                subject='You have been added as a mentor',
                message=(
                    f"Hi {name},\n\n"
                    f"You’ve been added as a mentor for the internship \"{internship.title}\" by {client_profile.company_name}.\n"
                    f"🔐 Temporary Password: {password}\n"
                    f"Login and update your profile to get started!\n\n"
                    f"- Team Xpora"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )
        else:
            if user.role != 'mentor':
                user.role = 'mentor'
                user.save()

        MentorAssignment.objects.get_or_create(
            user=user,
            internship=internship,
            defaults={'status': 'approved'}
        )

        return Response({'detail': 'Mentor added and assigned successfully.'})

# --------- MENTOR CREATES TASK ---------
class TaskCreateView(generics.CreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        assignment = MentorAssignment.objects.filter(user=user, status='approved').first()
        if not assignment:
            raise serializers.ValidationError("You are not assigned as a mentor yet.")

        serializer.save(mentor=assignment, internship=assignment.internship)

# views.py
class MentorDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'mentor':
            return Response({'detail': 'Not authorized'}, status=403)

        assignments = MentorAssignment.objects.filter(user=user, status='approved')
        internship_ids = assignments.values_list('internship_id', flat=True)

        internships = Internship.objects.filter(id__in=internship_ids)
        interns = Intern.objects.filter(internship_id__in=internship_ids, is_approved=True)
        tasks = Task.objects.filter(mentor__user=user)

        return Response({
            'internships': InternshipSerializer(internships, many=True).data,
            'interns': InternSerializer(interns, many=True).data,
            'tasks': TaskSerializer(tasks, many=True).data
        })
class ClientDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'client':
            return Response({'detail': 'Not authorized'}, status=403)

        internships = Internship.objects.filter(client=user)
        internship_ids = internships.values_list('id', flat=True)
        mentors = MentorAssignment.objects.filter(internship_id__in=internship_ids)

        return Response({
            'internships': InternshipSerializer(internships, many=True).data,
            'mentors': MentorAssignmentSerializer(mentors, many=True).data,
        })


# --------- INTERN TASK TRACKER ---------
class InternProgressView(generics.RetrieveAPIView):
    serializer_class = InternSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Intern, user=self.request.user)

class AdminInternProgressView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        interns = Intern.objects.filter(is_approved=True)
        data = []

        for intern in interns:
            total_tasks = Task.objects.filter(internship=intern.internship).count()
            submitted_tasks = TaskStatus.objects.filter(intern=intern, submitted=True).count()
            late_submissions = TaskStatus.objects.filter(intern=intern, submitted=True).filter(
                submission_date__gt=models.F('task__due_date')
            ).count()

            seriousness = "Low"
            if total_tasks == 0:
                seriousness = "No tasks assigned"
            elif submitted_tasks / total_tasks >= 0.8 and late_submissions == 0:
                seriousness = "High"
            elif submitted_tasks / total_tasks >= 0.5:
                seriousness = "Medium"

            data.append({
                "intern": intern.user.name,
                "email": intern.user.email,
                "internship": intern.internship.title,
                "tasks_assigned": total_tasks,
                "tasks_submitted": submitted_tasks,
                "late_submissions": late_submissions,
                "seriousness": seriousness
            })

        return Response(data)

class AdminReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_interns = Intern.objects.count()
        total_applications = Application.objects.count()
        completed_internships = Intern.objects.filter(status='completed').count()
        certificates_issued = Certificate.objects.count()

        return Response({
            "total_interns": total_interns,
            "total_applications": total_applications,
            "completed_internships": completed_internships,
            "certificates_issued": certificates_issued,
        })



class FeeCalculationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        application_count = Application.objects.filter(user=user).count()
        
        if application_count == 0:
            fee = 0  # First application is free
        else:
            fee = 100  # Subsequent applications cost $100 each
        
        return Response({'application_count': application_count, 'fee': fee})

class OfferLetterTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = OfferLetterTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OfferLetterTemplate.objects.filter(client__user=self.request.user)

    def perform_create(self, serializer):
        client_profile = get_object_or_404(ClientProfile, user=self.request.user)
        serializer.save(client=client_profile)

    @action(detail=False, methods=['get'])
    def my_templates(self, request):
        templates = OfferLetterTemplate.objects.filter(created_by=request.user)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)
    