# internship/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from internship.models import Intern
from users.models import CustomUser
from django.core.mail import send_mail
from django.conf import settings

import traceback
@receiver(post_save, sender=Intern)
def handle_intern_creation(sender, instance, created, **kwargs):
    print(f"Signal triggered for Intern: {instance}")
    
    user = instance.user
    internship = instance.internship
    print(f"Intern created: {user.email} for internship {internship.title}")

    if user.role in ['user', 'intern']:
        generated_password = f"{user.name.lower()}123"
        user.set_password(generated_password)
        user.role = 'intern'
        user.save()
        print(f"Generated password: {generated_password}")
        try:
            send_mail(
                subject='Internship Application Approved',
                message=f"""
Hi {user.name},

🎉 Your application for the internship "{internship.title}" from "{internship.client.company_name}" has been approved!

🔐 Your temporary password: {generated_password}

Please log in and get started!

- Team Xpora
""",
                from_email="xpora.website@gmail.com",
                recipient_list=[user.email],
                fail_silently=False,
            )
            print("✅ Email sent successfully from signal.")
        except Exception as e:
            print("❌ Email sending failed in signal:")
            import traceback
            traceback.print_exc()
    else:
        print(f"User role is already '{user.role}', skipping password/email.")
