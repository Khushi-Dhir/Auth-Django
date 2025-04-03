from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InternshipListView, InternshipDetailAPIView,get_mentor_id, 
    my_applications, apply_for_internship,TaskViewSet,get_internship_id,
    ApplicationViewSet, InternViewSet ,MentorProfileCreateView, MentorApplicationListView, MentorApplicationUpdateView
)

# ✅ Register viewsets with the router
router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'interns', InternViewSet, basename='intern')
router.register(r'tasks', TaskViewSet)
# router.register(r'mentor-applications', MentorApplicationViewSet, basename='mentor-application')
# router.register(r'mentor-profiles', MentorProfileViewSet, basename='mentor-profile')
# router.register(r'admin-mentor-applications', AdminMentorApplicationViewSet, basename='admin-mentor-application')

urlpatterns = [
    path('', include(router.urls)),  # Include ViewSet URLs
    path('internships/', InternshipListView.as_view(), name='internship-list'),
    path('internship-id/', get_internship_id, name='get_internship_id'),
    path('internships/<int:pk>/', InternshipDetailAPIView.as_view(), name='internship-detail'),  
    path('apply/<int:internship_id>/', apply_for_internship, name='apply_internship'),
    path('my-applications/', my_applications, name='my_applications'),
    path('mentor-id/', get_mentor_id, name='get_mentor_id'),
    path("mentor-profile/create/", MentorProfileCreateView.as_view(), name="mentor-profile-create"),
    path("mentor-applications/", MentorApplicationListView.as_view(), name="mentor-applications"),
    path("mentor-applications/<int:pk>/update/", MentorApplicationUpdateView.as_view(), name="mentor-application-update"),
    # path('mentors/',get_mentors, name='get_mentors'),               
    # path('mentors/<int:mentor_id>/', delete_mentor, name='delete_mentor'),
    # path('assign-mentor/<int:internship_id>/<int:mentor_id>/', assign_mentor_to_internship, name='assign_mentor'),
    # path('mentor/create-profile/', MentorProfileCreateView.as_view(), name='create_mentor_profile'),

]

