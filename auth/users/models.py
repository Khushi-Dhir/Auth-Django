# users/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, identify_hasher
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError("Email is required")
        if not name:
            raise ValueError("Name is required")
        user = self.model(email=self.normalize_email(email).lower(), name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email, name, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('client', 'Client'),
        ('mentor', 'Mentor'),
        ('intern', 'Intern'),
        ('user', 'User'),
    )
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = CustomUserManager()
    def save(self, *args, **kwargs):
        # Check if the password is already hashed; if not, hash it
        try:
            identify_hasher(self.password)
        except Exception:
            self.password = make_password(self.password)

        super().save(*args, **kwargs)


    def has_perm(self, perm, obj=None):
        return self.is_staff
    def __str__(self):
        return f"{self.name} ({self.role})"

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    skills = models.TextField(blank=True)
    github_link = models.URLField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    education = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.name}'s Profile"

    def is_complete(self):
        return all([
            self.skills,
            self.github_link,
            self.gender,
            self.resume,
            self.education,
            self.phone_number
        ])
