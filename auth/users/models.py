from django.db import models
from django.contrib.auth.models import AbstractBaseUser ,PermissionsMixin , BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not name:

            raise ValueError("Users must have a name")
        user = self.model(
            email=self.normalize_email(email).lower(),
            name=name,
        )
        if password and not password.startswith('pbkdf2_sha256$'):
            user.set_password(password)
        else:
            user.password = password
        user.is_active = False  
        user.is_staff = False 
        user.is_profile_completed = False
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password):
        user = self.create_user(email, name, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_profile_completed = True
        if password and not password.startswith('pbkdf2_sha256$'):
            user.set_password(password)
        else:
            user.password = password
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser,PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('mentor', 'Mentor'),
        ('intern', 'Intern'),
        ('user', 'User'),
    )
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_profile_completed = models.BooleanField(default=False)
         
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.name
   
    def get_short_name(self):
        return self.name
  
    def __str__(self):
        return f"{self.name} ({self.role})"
    

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    skills = models.TextField(help_text="Comma-separated skills")
    github_link = models.URLField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    resume = models.FileField(upload_to='resumes/')
    education = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.name}'s Profile"
