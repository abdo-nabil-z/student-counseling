from django.urls import path

from session.api.views import create_session


app_name = 'session_api'

urlpatterns = [
    path("create-session/", create_session, name="create-counselor"),
]
