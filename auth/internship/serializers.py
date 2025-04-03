from rest_framework import serializers
from .models import Internship , InternshipInfo, Application, Intern, Mentor, MentorProfile , MentorApplication, Task
from users.models import CustomUser
from rest_framework.exceptions import ValidationError


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'

class InternshipNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Internship
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'is_active']


class InternSerializer(serializers.ModelSerializer):
    # Include related internship details
    internship = InternshipNestedSerializer(read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Intern
        fields = [
            'id',
            'user_name',
            'user_email',
            'internship',
            'is_approved',
            'joined_at',
            'tasks_completed',
            'certificate_issued',
        ]

class InternshipInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipInfo
        fields = '__all__'


# ✅ Mentor Application Serializer
# class MentorApplicationSerializer(serializers.ModelSerializer):
#     internship_id = serializers.PrimaryKeyRelatedField(
#         queryset=Internship.objects.all(), 
#         source='internship', 
#         write_only=True
#     )

#     class Meta:
#         model = MentorApplication
#         fields = ['id', 'user', 'internship_id', 'status', 'applied_at']
#         read_only_fields = ['id', 'user', 'status', 'applied_at']

#     def create(self, validated_data):
#         """Create mentor application with current user and internship"""
#         user = self.context['request'].user
#         internship = validated_data['internship']

#         # Ensure only one application per internship per user
#         if MentorApplication.objects.filter(user=user, internship=internship).exists():
#             raise serializers.ValidationError("You have already applied for this internship as a mentor.")

#         application = MentorApplication.objects.create(
#             user=user,
#             internship=internship,
#             status='pending'
#         )
#         return application

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class MentorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        fields = ["id", "internship", "bio", "experience", "resume", "expertise", "status"]


# ✅ Mentor Application Serializer
class MentorApplicationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    internship_title = serializers.CharField(source="internship.title", read_only=True)

    class Meta:
        model = MentorApplication
        fields = ["id", "user", "user_name", "internship", "internship_title", "status", "applied_at"]

# class MentorApplicationSerializer(serializers.ModelSerializer):
#     internship_id = serializers.PrimaryKeyRelatedField(queryset=Internship.objects.all(), source='internship', write_only=True)

#     class Meta:
#         model = MentorApplication
#         fields = ['id', 'user', 'internship_id', 'status', 'applied_at']
#         read_only_fields = ['id', 'user', 'status', 'applied_at']

#     def create(self, validated_data):
#         """Create mentor application and associate it with the internship."""
#         user = self.context['request'].user
#         internship = validated_data['internship']

#         # Ensure the user is not applying for the same internship multiple times
#         if MentorApplication.objects.filter(user=user, internship=internship).exists():
#             raise serializers.ValidationError("You have already applied for this internship as a mentor.")

#         # Create the mentor application with a status of 'pending'
#         application = MentorApplication.objects.create(
#             user=user,
#             internship=internship,
#             status='pending'
#         )
#         return application

# ✅ Mentor Profile Serializer
# class MentorProfileSerializer(serializers.ModelSerializer):
#     internship_id = serializers.PrimaryKeyRelatedField(
#         queryset=Internship.objects.all(), 
#         source='internship', 
#         write_only=True
#     )

#     class Meta:
#         model = MentorProfile
#         fields = ['id', 'user', 'internship_id', 'bio', 'experience', 'resume', 'expertise', 'status', 'is_complete']
#         read_only_fields = ['id', 'user', 'status', 'is_complete']

#     def create(self, validated_data):
#         """Create mentor profile linked to internship"""
#         user = self.context['request'].user
#         internship = validated_data['internship']

#         # Ensure user has a mentor application and it is approved
#         application = MentorApplication.objects.filter(user=user, internship=internship, status='approved').first()
#         if not application:
#             raise serializers.ValidationError("You must have an approved application for this internship to create a mentor profile.")

#         profile = MentorProfile.objects.create(
#             user=user,
#             internship=internship,
#             **validated_data
#         )
#         return profile


# class MentorProfileSerializer(serializers.ModelSerializer):
#     internship_id = serializers.PrimaryKeyRelatedField(queryset=Internship.objects.all(), source='internship', write_only=True)

#     class Meta:
#         model = MentorProfile
#         fields = ['id', 'user', 'internship_id', 'bio', 'experience', 'resume', 'expertise', 'status', 'is_complete']
#         read_only_fields = ['id', 'user', 'status', 'is_complete']

#     def create(self, validated_data):
#         """Create mentor profile linked to internship."""
#         user = self.context['request'].user
#         internship = validated_data['internship']

#         # Ensure the user has an approved mentor application for the internship
#         # application = MentorApplication.objects.filter(user=user, internship=internship, status='approved').first()
#         # if not application:
#         #     raise serializers.ValidationError("You must have an approved mentor application for this internship to create a profile.")

#         # Create the mentor profile
#         profile = MentorProfile.objects.create(
#             user=user,
#             internship=internship,
#             **validated_data
#         )
#         return profile

# class MentorSerializer(serializers.ModelSerializer):
#     """Serializer for the Mentor model"""
#     user_name = serializers.CharField(source='user.name', read_only=True)
#     user_email = serializers.EmailField(source='user.email', read_only=True)

#     # ✅ Include related mentor profile fields
#     bio = serializers.CharField(source='user.mentor_profile.bio', read_only=True)
#     experience = serializers.IntegerField(source='user.mentor_profile.experience', read_only=True)
#     resume = serializers.FileField(source='user.mentor_profile.resume', read_only=True)
    
#     class Meta:
#         model = Mentor
#         fields = [
#             'id', 'user_name', 'user_email', 
#             'expertise', 'bio', 'experience', 'resume'
#         ]




class InternshipSerializer(serializers.ModelSerializer):
    current_interns = serializers.SerializerMethodField()
    skills = serializers.StringRelatedField(many=True)
    info = InternshipInfoSerializer()

    class Meta:
        model = Internship
        fields = [
            'id',
            'title',
            'description',
            'start_date',
            'end_date',
            'is_active',
            'capacity',
            'current_interns',
            'skills',
            'info',
        ]

    def get_current_interns(self, obj):
        return obj.interns.filter(is_approved=True).count()



