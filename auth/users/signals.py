from .models import UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from djoser.signals import user_registered
from django.conf import settings
from django.core.mail import send_mail
from djoser.utils import encode_uid
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()

@receiver(user_registered)
def send_custom_activation_email(sender, user, request, **kwargs):
    if user.is_active:
        return

    uid = encode_uid(user.pk)
    token = default_token_generator.make_token(user)
    activation_link = f"{settings.SITE_URL}/activate/{uid}/{token}"

    subject = "Activate Your Xpora Account"
    message = f"""
    Hi {user.name},

    Please click the link below to activate your account:

    {activation_link}

    This link is valid for only 24 hours.

    Thanks,
    Xpora Team
    """
    send_mail(subject, message, "xpora.website@gmail.com", [user.email])

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
