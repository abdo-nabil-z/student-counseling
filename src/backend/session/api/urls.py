from django.urls import path

from session.api.views import create_session


app_name = 'session_api'

urlpatterns = [
    path("create-session/", create_session, name="create-counselor"),
]
from django.urls import path
from session.api.views import create_session, list_sessions   # add list_sessions

app_name = "session_api"

urlpatterns = [
    path("", list_sessions, name="list-sessions"),                 # GET /api/session/
    path("create-session/", create_session, name="create-session"),
]