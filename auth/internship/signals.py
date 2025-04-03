# internship/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from users.models import CustomUser
from .models import MentorApplication, MentorProfile


@receiver(post_save, sender=MentorApplication)
def approve_mentor_application(sender, instance, created, **kwargs):
    """
    Signal to create mentor profile and send approval email
    """
    if instance.status == 'approved':
        user = instance.user

        # ✅ Create mentor profile if it doesn't exist
        MentorProfile.objects.get_or_create(
            user=user,
            internship=instance.internship,
            defaults={
                'bio': 'No bio provided',
                'experience': 0,
                'expertise': 'Not specified',
                'resume': None,
                'status': 'approved',
                'is_complete': False
            }
        )

        # ✅ Send approval email
        send_mail(
            subject='Mentor Application Approved',
            message=(
                f"Hello {user.name},\n\n"
                f"Your mentor application has been approved for the internship: {instance.internship.title}.\n"
                f"Please log in to your account to complete your profile and access mentor features.\n\n"
                f"🚀 Xpora Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
