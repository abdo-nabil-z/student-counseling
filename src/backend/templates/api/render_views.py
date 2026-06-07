
from rest_framework import status

from counselors.models import Counselor
from templates.models import Template
from templates.api.serializers import TemplateRenderTestmailRequestSerializer
from templates.api import schemas
from templates.context_registry import TestmailContext
from rest_framework.response import Response

from rest_framework.decorators import api_view


from django.shortcuts import get_object_or_404

from jinja2.sandbox import SandboxedEnvironment
from jinja2 import TemplateSyntaxError, UndefinedError, StrictUndefined, meta as jinja2_meta


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




@schemas.render_template_for_testmail
@api_view(["POST"])
def render_template_for_testmail(request):
    template_id = request.query_params.get("template_id")
    if not template_id:
        return Response({"error": "Template ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    template = get_object_or_404(Template, id=template_id)
    
    serializer = TemplateRenderTestmailRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    counselor_id = serializer.validated_data["counselor"]
    if not Counselor.objects.filter(id=counselor_id).exists():
        return Response({"error": "Counselor not found"}, status=status.HTTP_404_NOT_FOUND)

    ctx = TestmailContext.build(counselor_id=counselor_id)
    try:
        rendered = render_from_template(template.content, **ctx.model_dump())
    except TemplateRenderError as e:
        return Response({"error": e.to_dict()}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return Response({"rendered": rendered}, status=status.HTTP_200_OK)
