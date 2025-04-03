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
urlpatterns += [
    re_path(r'^(?!api|auth|user/).*$', TemplateView.as_view(template_name='index.html')),
]
