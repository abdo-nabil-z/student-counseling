"""
URL configuration for consultation_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

handler404 = "consultation_backend.error_handlers.api_not_found"
handler500 = "consultation_backend.error_handlers.api_server_error"

urlpatterns = [
    # Apps Urls
    path('admin/', admin.site.urls),
    path('counselors/', include('counselors.urls', namespace='counselors')),
    path('students/', include('students.urls', namespace='students')),
    path('appointments/', include('appointments.urls', namespace='appointments')),

    # REST Framwork Urls
    path('api/counselors/', include('counselors.api.urls', namespace='counselors_api')),
    path('api/students/', include('students.api.urls', namespace='students_api')),
    path('api/appointments/', include('appointments.api.urls', namespace='appointments_api')),
    path('api/documents/', include('documents.api.urls', namespace='documents_api')),
    path('api/templates/', include('templates.api.urls', namespace='templates_api')),


    # documentation urls
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
