from django.contrib import admin
from .models import   Internship, Application, Intern, Task,MentorAssignment, Skill, PaymentProof,ClientProfile, TaskStatus, OfferLetterTemplate, Certificate, InternshipSchedule

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'company_name', 'industry', 'contact_number']
    search_fields = ['user__email', 'company_name', 'industry']

@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'client', 'start_date', 'end_date', 'is_active', 'capacity']
    list_filter = ['is_active', 'start_date']
    search_fields = ['title', 'client__user__email']
    filter_horizontal = ['skills']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'internship', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['user__email', 'internship__title']

@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ['id', 'application', 'verified', 'uploaded_at']
    list_filter = ['verified']
    search_fields = ['application__user__email']
    readonly_fields = ['uploaded_at']

@admin.register(Intern)
class InternAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'internship', 'is_approved', 'joined_at', 'is_completed', 'certificate_issued']
    list_filter = ['is_approved', 'is_completed', 'certificate_issued']
    search_fields = ['user__email', 'internship__title']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'internship', 'mentor', 'due_date', 'created_at']
    list_filter = ['due_date']
    search_fields = ['title', 'mentor__user__email']

@admin.register(MentorAssignment)
class MentorAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'internship', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__email', 'internship__title']

@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'intern', 'task', 'submitted', 'submission_date']
    list_filter = ['submitted']
    search_fields = ['intern__user__email', 'task__title']

@admin.register(OfferLetterTemplate)
class OfferLetterTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'date']
    search_fields = ['client__email']

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'user', 'internship', 'issued_at', 'is_approved_by_mentor']
    list_filter = ['is_approved_by_mentor', 'issued_at']
    search_fields = ['user__email', 'internship__title']

@admin.register(InternshipSchedule)
class InternshipScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'internship', 'start_date', 'end_date', 'title', 'zoom_link']
    list_filter = ['start_date', 'end_date']
    search_fields = ['internship__title', 'title'] 