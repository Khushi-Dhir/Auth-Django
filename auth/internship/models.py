from django.db import models
from django.core.exceptions import ValidationError
from users.models import CustomUser


# ✅ Skill Model
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# ✅ Internship Model (Declared First to Avoid Circular Dependency)
class Internship(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    skills = models.ManyToManyField(Skill, related_name='internships')
    capacity = models.PositiveIntegerField(default=10)
    zoom_link = models.URLField(blank=True, null=True)
    task_instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title}"

    def is_full(self):
        """Check if the internship has reached its capacity"""
        return self.interns.filter(is_approved=True).count() >= self.capacity


# ✅ Internship Info Model
class InternshipInfo(models.Model):
    internship = models.OneToOneField(Internship, on_delete=models.CASCADE, related_name='info')
    description = models.CharField(max_length=255, blank=True, null=True)
    eligibility = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)  # e.g., "2 months"
    stipend = models.CharField(max_length=50, blank=True, null=True)   # e.g., "₹5000/month"
    apply_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Info for {self.internship.title}"


# ✅ Mentor Profile Model
class MentorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='mentor_profile')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='mentor_profiles')
    
    bio = models.TextField(blank=True, null=True)
    experience = models.PositiveIntegerField(default=0)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    expertise = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10, 
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], 
        default='pending'
    )

    def clean(self):
        """Ensure only one profile per user and enforce internship link."""
        if MentorProfile.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            raise ValidationError("This user already has a mentor profile.")

    def save(self, *args, **kwargs):
        """Auto-complete check before saving."""
        self.is_complete = bool(self.resume and self.expertise and self.bio and self.experience)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mentor: {self.user.name} for {self.internship.title}"


# ✅ Mentor Model
class Mentor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='mentor_data')

    def clean(self):
        """Ensure only users with 'mentor' role can be mentors"""
        if self.user.role != 'mentor':
            raise ValidationError("Only users with the 'mentor' role can be assigned as a mentor.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mentor: {self.user.name}"


# ✅ Mentor Application Model
class MentorApplication(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mentor_applications')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='mentor_applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        If approved, change user role to mentor.
        """
        super().save(*args, **kwargs)

        if self.status == 'approved':
            self.user.role = 'mentor'
            self.user.save()
        MentorProfile.objects.get_or_create(user=self.user, internship=self.internship)

    def __str__(self):
        return f"{self.user.name} → {self.internship.title} ({self.status})"


# ✅ Application Model
class Application(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )

    class Meta:
        unique_together = ('user', 'internship')

    def __str__(self):
        return f"Application: {self.user.name} for {self.internship.title}"


# ✅ Intern Model
class Intern(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='intern_profile')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='interns')
    is_approved = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    tasks_completed = models.PositiveIntegerField(default=0)
    certificate_issued = models.BooleanField(default=False)

    def clean(self):
        """Ensure only users with 'intern' role can be linked"""
        if self.user.role != 'intern':
            self.user.role = 'intern'
            self.user.save()

        # Check if the internship is full
        if self.internship.is_full():
            raise ValidationError("This internship is already full.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Intern: {self.user.name} in {self.internship.title}"


# ✅ Task Model
class Task(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='tasks')
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='assigned_tasks')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Task: {self.title} by {self.mentor.user.name}"
