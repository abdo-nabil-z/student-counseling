from django.urls import path

from templates.api.views import (
    list_templates,
    get_template,
    update_template,
    purpose_context_schema,
    render_testmail,
    render_student_invitation,
    render_student_reminder,
    render_forced_appointment_assignment,
    render_appointment_invitation,
    render_counselor_preparation_instruction,
    render_appointment_cancellation,
    render_study_plan,
    render_appointment_minutes,
)

app_name = 'templates_api'

urlpatterns = [
    # Template CRUD (keyed by purpose)
    path("", list_templates, name="list_templates"),
    path("<str:purpose>/", get_template, name="get_template"),
    path("<str:purpose>/update/", update_template, name="update_template"),
    path("<str:purpose>/context-schema/", purpose_context_schema, name="purpose_context_schema"),

    # Render endpoints (one per purpose, before the <str:purpose>/ catch-all)
    path("testmail/render/", render_testmail, name="render_testmail"),
    path("student_invitation/render/", render_student_invitation, name="render_student_invitation"),
    path("student_reminder/render/", render_student_reminder, name="render_student_reminder"),
    path("forced_appointment_assignment/render/", render_forced_appointment_assignment, name="render_forced_appointment_assignment"),
    path("appointment_invitation/render/", render_appointment_invitation, name="render_appointment_invitation"),
    path("counselor_preparation_instruction/render/", render_counselor_preparation_instruction, name="render_counselor_preparation_instruction"),
    path("appointment_cancellation/render/", render_appointment_cancellation, name="render_appointment_cancellation"),
    path("study_plan/render/", render_study_plan, name="render_study_plan"),
    path("appointment_minutes/render/", render_appointment_minutes, name="render_appointment_minutes"),
]

