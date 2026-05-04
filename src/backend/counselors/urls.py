from django.urls import path

from . import views

app_name = 'counselors'

#  clinic/   or   clinic:

urlpatterns = [
    path('', views.home ,name='home'),
]
