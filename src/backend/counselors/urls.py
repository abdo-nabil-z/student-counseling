from django.urls import path

from counselors.views import home

app_name = 'counselors'

#  counselors/   or   counselors:

urlpatterns = [
    path('', home ,name='home'),
]
