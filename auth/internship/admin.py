# internship/admin.py
from django.contrib import admin
from .models import Mentor, Skill, Internship, Intern, InternshipInfo, Application, MentorProfile, MentorApplication, Task
from django.db import transaction


@admin.action(description='Approve selected interns and update user roles')
def approve_interns(modeladmin, request, queryset):
    """
    Approves interns and updates their user roles to 'intern'
    """
    for intern in queryset:
        if not intern.is_approved and not intern.internship.is_full():
            with transaction.atomic():
                intern.is_approved = True
                intern.save()

                # ✅ Update user role immediately
                user = intern.user
                if user.role != 'intern':
                    user.role = 'intern'
                    user.save()


class InternAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_role', 'internship', 'is_approved', 'joined_at')
    actions = [approve_interns]

    def user_role(self, obj):
        return obj.user.role

    user_role.short_description = "User Role"


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'experience', 'is_complete')
    list_filter = ('status', 'is_complete')
    search_fields = ('user__name', 'user__email')
    actions = ['approve_profiles', 'reject_profiles']

    @admin.action(description='Approve selected profiles')
    def approve_profiles(self, request, queryset):
        for profile in queryset:
            profile.status = 'approved'
            profile.save()

    @admin.action(description='Reject selected profiles')
    def reject_profiles(self, request, queryset):
        for profile in queryset:
            profile.status = 'rejected'
            profile.save()


@admin.register(MentorApplication)
class MentorApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'internship', 'status', 'applied_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'internship__title')


# ✅ Register models
admin.site.register(Task)
admin.site.register(Mentor)
admin.site.register(Skill)
admin.site.register(Internship)
admin.site.register(InternshipInfo)
admin.site.register(Intern, InternAdmin)
admin.site.register(Application)
