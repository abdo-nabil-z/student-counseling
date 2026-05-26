from django.urls import path

from templates.api.views import (
    templates_by_purpose,
    create_template,
    update_template,
    delete_template,
    purposes_list,
    set_default_template,
    generate_template_for_testmail,
)

app_name = 'templates_api'

urlpatterns = [
    # Templates
    path("templates/", templates_by_purpose, name="templates_by_purpose"),
    path("templates/create/", create_template, name="create_template"),
    path("templates/<int:template_id>/", update_template, name="update_template"),
    path("templates/<int:template_id>/delete/", delete_template, name="delete_template"),

    # Purposes (enum-based — no create/delete)
    path("purposes/", purposes_list, name="purposes_list"),
    path("purposes/<str:purpose>/set-default/", set_default_template, name="set_default_template"),

    # Generation
    path("generate/testmail/", generate_template_for_testmail, name="generate_testmail"),
]

