from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'offer-letter-templates', OfferLetterTemplateViewSet, basename='offerlettertemplate')

urlpatterns = [
    path('', include(router.urls)),   
    path("skills/", SkillListAPIView.as_view(), name="skill-list"),
    # Internship browsing
    path('internships/', InternshipListView.as_view(), name='internship-list'),
    path('my-internship/', MyInternshipView.as_view(), name='my-internship'),
    path('client/internships/', ClientInternshipListView.as_view(), name='client-internship-list'),
    path('internships/<int:pk>/', InternshipDetailView.as_view(), name='internship-detail'),
    path('client/create-internship/', CreateInternshipView.as_view(), name='create-internship'),
    path('client/add-mentor/', AddMentorByClientView.as_view(), name='add-mentor-by-client'),
    path('create-client-profile/', CreateClientProfileView.as_view(), name='create-client-profile'),
    path('internships/latest/', LatestInternshipView.as_view(), name='latest-internship'),

    path('calculate-fee/', FeeCalculationView.as_view(), name='calculate-fee'),
    # path('interns/<int:internship_id>/offerletter/', OfferLetterPDFView.as_view(), name='offer-letter'),
    # Intern application
    path('user-applications/', UserApplicationsView.as_view(), name='user-applications'),
    path('apply/', ApplyToInternshipView.as_view(), name='apply-internship'),
    path('upload-payment/', UploadPaymentProofView.as_view(), name='upload-payment-proof'),
    path('verify-payment/<int:pk>/', VerifyPaymentProofView.as_view(), name='verify-payment'),
    path('internships/<int:internship_id>/generate-schedule/', GenerateScheduleView.as_view(), name='generate-schedule'),
    path('internships/<int:internship_id>/schedule/', ScheduleListView.as_view(), name='list-schedule'),
    path('schedule/<int:id>/update/', ScheduleUpdateView.as_view(), name='update-schedule-item'),
    # Mentor actions
    path('mentor/apply/', MentorAssignmentView.as_view(), name='mentor-assignment'),
    path('mentor/schedules/', MentorScheduleListView.as_view(), name='mentor-schedules'),
    path('mentor/task/setup/', MentorTaskSetupView.as_view(), name='mentor-task-setup'),
    path('intern/task/submit/', InternTaskSubmissionView.as_view(), name='intern-task-submit'),
    path('mentor/task/update/<int:id>/', MentorTaskUpdateView.as_view(), name='mentor-task-update'),
    path('mentor/task/review/<int:id>/', MentorTaskReviewView.as_view(), name='mentor-task-review'),
    path('intern/task/status/', TaskStatusListView.as_view(), name='intern-task-status'),
    path('mentor/task/status/', MentorTaskStatusListView.as_view(), name='mentor-task-status'),
    # Mentor dashboard
    path('mentor/dashboard/', MentorDashboardView.as_view(), name='mentor-dashboard'),
    path('payment-proofs/', PaymentProofListView.as_view(), name='payment-proofs'),
    # Client dashboard
    path('client/dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('mentor/certificates/<uuid:certificate_id>/approve/', approve_certificate, name='approve-certificate'),
    path('mentor/certificates/', mentor_certificates),
    # Intern dashboard 
    path('intern/progress/', InternProgressView.as_view(), name='intern-progress'),
    path('admin/intern-progress/', AdminInternProgressView.as_view(), name='admin-intern-progress'),
    path("admin/report/", AdminReportView.as_view(), name="admin-report"),
    path('offer-letter-pdf/<int:internship_id>/', OfferLetterPDFView.as_view(), name='offer-letter-pdf'),
    path('offer-letters/<int:internship_id>/', generate_offer_letter_pdf, name='download_offer_letter'),
    path('certificate/download/<int:internship_id>/', CertificatePDFView.as_view(), name='certificate-download'),
    path('reports/', ReportsView.as_view(), name='reports'),
    path('clients/unverified/', unverified_clients, name='unverified-clients'),
    path('admin/verify-client/<int:user_id>/', verify_client, name='verify-client'),
]
