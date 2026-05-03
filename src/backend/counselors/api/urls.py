from django.urls import path

from counselors.api.views import api_dummy


app_name = 'counselors_api'


urlpatterns = [
    path('echo-data/', api_dummy, name='echo-data'),
]
