from django.urls import path

from templates.api.views import (
    list_templates,
    get_template,
    update_template,
    purpose_context_schema,
    render_purpose,
)

app_name = 'templates_api'

urlpatterns = [
    # Template CRUD (keyed by purpose)
    path("", list_templates, name="list_templates"),
    path("<str:purpose>/", get_template, name="get_template"),
    path("<str:purpose>/update/", update_template, name="update_template"),
    path("<str:purpose>/context-schema/", purpose_context_schema, name="purpose_context_schema"),

    # Render endpoint (single generic view, dispatches per purpose)
    path("<str:purpose>/render/", render_purpose, name="render_purpose"),
]

