# Updated Models (with intern submissions, mentor evaluation, and reporting logic)
from django.db import models
from django.core.exceptions import ValidationError
from users.models import CustomUser
from django.conf import settings
import uuid

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class ClientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    logo = models.ImageField(upload_to='client_logos/', blank=True, null=True)
    signature = models.ImageField(upload_to='client_signatures/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    pin_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.company_name

class Internship(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    project_description = models.TextField(blank=True, null=True)
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='internships', null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    skills = models.ManyToManyField(Skill, blank=True)
    capacity = models.PositiveIntegerField(default=10)
    zoom_link = models.URLField(blank=True, null=True)
    task_instructions = models.TextField(blank=True, null=True)
    eligibility = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    stipend = models.CharField(max_length=50, blank=True, null=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    upi_id = models.CharField(max_length=100, default='khushidhir54@okicici')

    def __str__(self):
        return self.title

    def is_full(self):
        return self.interns.filter(is_approved=True).count() >= self.capacity

    def seats_left(self):
        approved_interns = self.interns.filter(is_approved=True).count()
        return self.capacity - approved_interns

class MentorAssignment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mentor_assignments')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='assigned_mentors')
    bio = models.TextField(blank=True, null=True)
    experience = models.PositiveIntegerField(default=0)
    resume = models.FileField(upload_to='mentor_resumes/', blank=True, null=True)
    expertise = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = MentorAssignment.objects.get(pk=self.pk).status
        super().save(*args, **kwargs)
        if self.status == 'approved' and previous_status != 'approved':
            self.user.role = 'mentor'
            self.user.save()


    def __str__(self):
        return f"{self.user.name} ({self.status}) → {self.internship.title}"

class PaymentProof(models.Model):
    application = models.OneToOneField('Application', on_delete=models.CASCADE, related_name='payment_proof')
    upi_screenshot = models.ImageField(upload_to='payment_screenshots/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment by {self.application.user.name} for {self.application.internship.title}"

class Application(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications')
    is_first_internship = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'internship')

    def __str__(self):
        return f"{self.user.name} → {self.internship.title} ({self.status})"

class Intern(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='intern_profile')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='interns')
    is_approved = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    tasks_completed = models.PositiveIntegerField(default=0)
    certificate_approval = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)
    has_paid_once = models.BooleanField(default=False)

    def clean(self):
        if self.internship.is_full() and not self.is_approved:
            raise ValidationError("Internship is already full.")
        if self.user.role != 'intern':
            self.user.role = 'intern'
            self.user.save()

    def save(self, *args, **kwargs):
        if self.user.role != 'intern':
            self.user.role = 'intern'
            self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.name} in {self.internship.title}"

class Task(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='tasks')
    mentor = models.ForeignKey(MentorAssignment, on_delete=models.CASCADE, related_name='tasks')
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, related_name='tasks', null=True)
    week_number = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    github_link = models.URLField(blank=True, null=True)  
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.mentor.user.name})"

class TaskStatus(models.Model):
    intern = models.ForeignKey('Intern', on_delete=models.CASCADE, related_name='task_statuses')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='statuses')
    submitted = models.BooleanField(default=False)
    github_link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    submission_date = models.DateTimeField(null=True, blank=True)
    mentor_reviewed = models.BooleanField(default=False)
    marked_completed = models.BooleanField(default=False)

    def is_late(self):
        return self.submitted and self.submission_date and self.submission_date.date() > self.task.due_date

    def __str__(self):
        status = "Submitted" if self.submitted else "Pending"
        return f"{self.intern.user.name} - {self.task.title} ({status})"

class OfferLetterTemplate(models.Model):
    client = models.OneToOneField(ClientProfile, on_delete=models.CASCADE)
    editable_section = models.TextField(default="This is the editable section of the offer letter.")
    signature_name = models.CharField(max_length=255, blank=True, null=True)
    signature_image = models.ImageField(upload_to='signatures/', blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Offer Letter Template - {self.client.company_name}"

    def generate_full_body(self, intern_name, internship):
        top = f"""
Dear {intern_name},

We are pleased to offer you an internship at {self.client.company_name}.
Your internship will begin on {internship.start_date} and conclude on {internship.end_date}.
"""
        bottom = f"""
Please accept this offer by replying to this email. We look forward to having you on our team.

Sincerely,
{self.signature_name or self.client.user.name}
"""
        return top + self.editable_section + bottom

class Certificate(models.Model):
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    internship = models.ForeignKey('Internship', on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)
    is_approved_by_mentor = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)
    download_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Certificate for {self.user.name} - {self.internship.title}"

    def generate_certificate_text(self):
        return f"""
        CERTIFICATE OF INTERNSHIP

        This is to certify that {self.user.name} has successfully completed the internship
        at {self.internship.client.company_name} from {self.internship.start_date} to {self.internship.end_date}
        as part of the internship program organized by Xpora.

        The internship focused on {self.internship.title}, during which the intern demonstrated
        exceptional dedication and successfully fulfilled all the assigned tasks and responsibilities.

        Issued on: {self.issued_at.date()}

        Signed,
        {self.internship.client.company_name}
        (Xpora)
        """


class InternshipSchedule(models.Model):
    internship = models.ForeignKey('Internship', on_delete=models.CASCADE, related_name='schedule')
    week_number = models.IntegerField()
    title = models.CharField(max_length=100)
    zoom_link = models.URLField(blank=True, default='http://zoom.com/')
    start_date = models.DateField()
    end_date = models.DateField()
    resources = models.TextField(blank=True, null=True)  # optional links/docs
    is_mandatory = models.BooleanField(default=True)

    def __str__(self):
        return f"Week {self.week_number} - {self.title}"
