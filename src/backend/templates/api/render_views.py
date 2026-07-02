from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

from jinja2.sandbox import SandboxedEnvironment
from jinja2 import TemplateSyntaxError, UndefinedError, StrictUndefined, meta as jinja2_meta

from templates.models import Template, Purpose
from templates.api import schemas
from templates.api.serializers import (
    CounselorRenderSerializer,
    StudentRenderSerializer,
    StudentCounselorRenderSerializer,
)
from templates.context_registry import (
    TestmailContext,
    StudentAndBlocksContext,
    AppointmentStudentCounselorContext,
    StudyPlanContext,
    AppointmentMinutesContext,
)


class TemplateRenderError(Exception):
    def __init__(self, error_type, message, line=None, variable=None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.line = line
        self.variable = variable

    def to_dict(self):
        d = {"type": self.error_type, "message": self.message}
        if self.line is not None:
            d["line"] = self.line
        if self.variable is not None:
            d["variable"] = self.variable
        return d


def render_from_template(template_str, **context):
    env = SandboxedEnvironment(undefined=StrictUndefined)
    try:
        ast = env.parse(template_str)
    except TemplateSyntaxError as e:
        raise TemplateRenderError("syntax_error", e.message, line=e.lineno)

    undeclared = jinja2_meta.find_undeclared_variables(ast)
    missing = undeclared - set(context.keys())
    if missing:
        var = sorted(missing)[0]
        raise TemplateRenderError(
            "undefined_variable",
            f"Variable '{var}' is not available in this context",
            variable=var,
        )

    try:
        return env.from_string(template_str).render(**context)
    except UndefinedError as e:
        raise TemplateRenderError("undefined_variable", str(e))


def _render_purpose(request, purpose, serializer_class, context_class):
    template = get_object_or_404(Template, purpose=purpose)
    serializer = serializer_class(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        ctx = context_class.build(**serializer.validated_data)
    except NotImplementedError as e:
        return Response({"error": str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)
    try:
        rendered = render_from_template(template.content, **ctx.model_dump())
    except TemplateRenderError as e:
        return Response({"error": e.to_dict()}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response({"rendered": rendered}, status=status.HTTP_200_OK)


@schemas.render_testmail
@api_view(["POST"])
def render_testmail(request):
    return _render_purpose(request, Purpose.TESTMAIL, CounselorRenderSerializer, TestmailContext)


@schemas.render_student_invitation
@api_view(["POST"])
def render_student_invitation(request):
    return _render_purpose(request, Purpose.STUDENT_INVITATION_MAIL, StudentRenderSerializer, StudentAndBlocksContext)


@schemas.render_student_reminder
@api_view(["POST"])
def render_student_reminder(request):
    return _render_purpose(request, Purpose.STUDENT_REMINDER_MAIL, StudentRenderSerializer, StudentAndBlocksContext)


@schemas.render_forced_appointment_assignment
@api_view(["POST"])
def render_forced_appointment_assignment(request):
    return _render_purpose(request, Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_appointment_invitation
@api_view(["POST"])
def render_appointment_invitation(request):
    return _render_purpose(request, Purpose.APPOINTMENT_INVITATION_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_counselor_preparation_instruction
@api_view(["POST"])
def render_counselor_preparation_instruction(request):
    return _render_purpose(request, Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_appointment_cancellation
@api_view(["POST"])
def render_appointment_cancellation(request):
    return _render_purpose(request, Purpose.APPOINTMENT_CANCELLATION_MAIL, StudentCounselorRenderSerializer, AppointmentStudentCounselorContext)


@schemas.render_study_plan
@api_view(["POST"])
def render_study_plan(request):
    return _render_purpose(request, Purpose.STUDY_PLAN, StudentRenderSerializer, StudyPlanContext)


@schemas.render_appointment_minutes
@api_view(["POST"])
def render_appointment_minutes(request):
    return _render_purpose(request, Purpose.APPOINTMENT_MINUTES, StudentCounselorRenderSerializer, AppointmentMinutesContext)

