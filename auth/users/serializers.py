from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import UserProfile ,CustomUser
from internship.models import MentorAssignment, Application, Internship, Certificate

User = get_user_model()


class UserInternshipSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='internship.title')

    class Meta:
        model = Application
        fields = ['title', 'status']

class UserMentorInternshipSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='internship.title')

    class Meta:
        model = MentorAssignment
        fields = ['title', 'status']

class CustomUserDetailSerializer(serializers.ModelSerializer):
    role = serializers.CharField()
    internships_as_intern = serializers.SerializerMethodField()
    internships_as_mentor = serializers.SerializerMethodField()
    certificates_issued = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'role', 'internships_as_intern', 'internships_as_mentor', 'certificates_issued','created_at' ]

    def get_internships_as_intern(self, user):
        try:
            apps = Application.objects.filter(user=user)
            return UserInternshipSerializer(apps, many=True).data
        except Exception as e:
            print("❌ Error in internships_as_intern:", e)
            return []

    def get_internships_as_mentor(self, user):
        try:
            assignments = MentorAssignment.objects.filter(user=user)
            return UserMentorInternshipSerializer(assignments, many=True).data
        except Exception as e:
            print("❌ Error in internships_as_mentor:", e)
            return []

    def get_certificates_issued(self, user):
        try:
            return Certificate.objects.filter(user=user).exists()
        except Exception as e:
            print("❌ Error in certificates_issued:", e)
            return False



class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
}

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['user']
        
    def update(self, instance, validated_data):
        resume = self.context['request'].FILES.get('resume')
        if resume:
            instance.resume = resume
        return super().update(instance, validated_data)

    def validate_skills(self, value):
        skills = [skill.strip() for skill in value.split(',')]
        return ', '.join(skills)
