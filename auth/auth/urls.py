from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/', include('djoser.urls.authtoken')),
    path('user/', include('users.urls')),
    path('api/', include('internship.urls')),  # Ensure API is defined before the catch-all
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Ensure this is the LAST path
# urlpatterns += [
#     re_path(r'^(?!api|auth|user/).*$', TemplateView.as_view(template_name='index.html')),
# ]


def custom_404_view(request, exception=None):
    return JsonResponse({'error': 'Not found'}, status=404)

handler404 = 'auth.urls.custom_404_view'  # Replace 'project_name' with your project folder name
