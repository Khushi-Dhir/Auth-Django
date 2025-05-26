from rest_framework import serializers
from .models import (
    Internship, Application, Intern, Task, MentorAssignment,
    Skill, PaymentProof, TaskStatus, ClientProfile,
    Certificate, OfferLetterTemplate, InternshipSchedule
)
from users.models import CustomUser



class InternshipScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipSchedule
        fields = '__all__'


# =============================
# Skill Serializer
# =============================
class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']


# =============================
# Client Profile Serializer
# =============================
class ClientProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    class Meta:
        model = ClientProfile
        fields = [
            'id', 'company_name', 'website', 'industry',
            'contact_number', 'city', 'state', 'country',
            'description', 'username', 'user_id'
        ]
        read_only_fields = ['user']


# =============================
# Mentor Assignment Serializer
# =============================
class MentorAssignmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    internship_title = serializers.CharField(source='internship.title', read_only=True)

    class Meta:
        model = MentorAssignment
        fields = [
            'id', 'user', 'user_name', 'internship', 'internship_title',
            'bio', 'experience', 'resume', 'expertise',
            'status', 'created_at'
        ]
        read_only_fields = ['status', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else validated_data.get('user')
        internship = validated_data.get('internship')

        # Prevent duplicate assignments
        if MentorAssignment.objects.filter(user=user, internship=internship).exists():
            raise serializers.ValidationError("You have already applied as a mentor for this internship.")

        return MentorAssignment.objects.create(user=user, **validated_data)

# =============================
# Internship Serializer
# =============================
class InternshipSerializer(serializers.ModelSerializer):
    current_interns = serializers.SerializerMethodField()
    skills = SkillSerializer(many=True, read_only=True)
    assigned_mentors = MentorAssignmentSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        write_only=True,
        source='skills'
    )

    class Meta:
        model = Internship
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'is_active', 'capacity', 'current_interns',
            'skills', 'skill_ids','assigned_mentors',
            'zoom_link', 'task_instructions', 'eligibility',
            'benefits', 'responsibilities', 'duration', 'stipend',
            'fee', 'upi_id','project_description'
        ]
        read_only_fields = ['upi_id', 'fee']

    def get_current_interns(self, obj):
        return obj.interns.filter(is_approved=True).count()



# =============================
# Application Serializer
# =============================
class ApplicationSerializer(serializers.ModelSerializer):
    internship_title = serializers.CharField(source="internship.title", read_only=True)
    is_first_internship = serializers.BooleanField(read_only=True)
    class Meta:
        model = Application
        fields = ['id', 'user', 'internship', 'internship_title', 'status', 'applied_at','is_first_internship']
        read_only_fields = ['status', 'applied_at', 'is_first_internship']

    def validate(self, data):
        user = self.context['request'].user
        internship = data['internship']
        
        # If it's not the first internship and payment_proof is missing
        has_previous = Application.objects.filter(user=user, status='approved').exists()

        
        return data


# =============================
# Payment Proof Serializer
# =============================
class PaymentProofSerializer(serializers.ModelSerializer):
    internship_title = serializers.CharField(source='application.internship.title', read_only=True)
    user_email = serializers.EmailField(source='application.user.email', read_only=True)
    internship_id = serializers.IntegerField(source='application.internship.id', read_only=True)
    user_name = serializers.CharField(source='application.user.name', read_only=True)

    class Meta:
        model = PaymentProof
        fields = ['id', 'application', 'upi_screenshot', 'uploaded_at', 'verified', 'user_name', 'internship_title', 'user_email', 'internship_id']
        read_only_fields = ['uploaded_at']

    def validate_upi_screenshot(self, file):
        if not file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.pdf')):
            raise serializers.ValidationError("Unsupported file format.")
        return file


# =============================
# Intern Serializer
# =============================
class InternSerializer(serializers.ModelSerializer):
    internship_title = serializers.CharField(source="internship.title", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Intern
        fields = [
            'id', 'user', 'user_name', 'user_email', 'internship', 'internship_title',
            'is_approved', 'joined_at', 'tasks_completed','has_paid_once',
            'is_completed', 'certificate_approval', 'certificate_issued'
        ]
        read_only_fields = [
            'joined_at', 'user_name', 'user_email', 
            'internship_title', 'internship', 'user'
        ]


# =============================
# Task Serializer
# =============================
class TaskSerializer(serializers.ModelSerializer):
    mentor_name = serializers.CharField(source="mentor.user.name", read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'internship', 'mentor', 'mentor_name',
            'title', 'github_link', 'description',
            'due_date', 'created_at'
        ]
        read_only_fields = [
            'mentor', 'internship', 'mentor_name',
            'title', 'due_date', 'created_at'
        ]



# =============================
# Task Status Serializer
# =============================
class TaskStatusSerializer(serializers.ModelSerializer):
    intern_name = serializers.CharField(source="intern.user.name", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)
    is_late = serializers.SerializerMethodField()

    class Meta:
        model = TaskStatus
        fields = [
            'id', 'task', 'intern_name', 'task_title', 'submitted', 'submission_date',
            'is_late', 'description', 'github_link', 'marked_completed', 'mentor_reviewed'
        ]
        read_only_fields = ['submission_date', 'is_late']
    def get_is_late(self, obj):
        return obj.is_late() 




# =============================
# Certificate Serializer
# =============================
class CertificateSerializer(serializers.ModelSerializer):
    internship_title = serializers.CharField(source='internship.title', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    download_link = serializers.SerializerMethodField()


    class Meta:
        model = Certificate
        fields = [
            'certificate_id', 'user_name', 'internship_title',
            'issued_at', 'is_approved_by_mentor', 'download_count',
            'download_link'
        ]
        read_only_fields = ['issued_at', 'download_count']

    def get_download_link(self, obj):
        request = self.context.get('request')
        if obj.download_link:
            return request.build_absolute_uri(obj.download_link.url)
        return None


# =============================
# Offer Letter Template Serializer
# =============================
class OfferLetterTemplateSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)

    class Meta:
        model = OfferLetterTemplate
        fields = ['id', 'client', 'client_name', 'editable_section', 'signature_name', 'signature_image', 'date']
        read_only_fields = ['date']
