"""
Shared Jinja2 rendering primitives for the templates app.

The Jinja2 environment (and its {% checkbox %}/{% textfield %}/{% textbox %}/
{% signature %}/{% vspace %} form-field tags) is general — available to any
template regardless of purpose. `render_from_template` renders straight to
text (used for emails). `render_with_wrapper` additionally glues static
prepend/append text around the template source before rendering — used by
the `pdf` app to wrap Markdown content with its HTML/CSS page boilerplate.
"""
from dataclasses import dataclass, field

from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import TemplateSyntaxError, UndefinedError, StrictUndefined, meta as jinja2_meta
from markupsafe import Markup, escape
from pydantic import BaseModel

LINE_H_PT = 18  # one text line in pt, used by {% vspace %}


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


class FormFieldExtension(Extension):
    """Adds {% checkbox %}, {% textfield %}, {% textbox %}, {% signature %}, {% vspace %} tags."""

    tags = frozenset(["checkbox", "textfield", "textbox", "signature", "vspace"])

    def __init__(self, environment):
        super().__init__(environment)
        self._counters: dict[str, int] = {}
        self._prefill: dict[str, object] = {}
        environment.globals["_form_render"] = self._render

    def parse(self, parser):
        tag = parser.stream.current.value
        lineno = next(parser.stream).lineno

        kwargs = []
        while not parser.stream.current.test("block_end"):
            key = parser.stream.expect("name").value
            parser.stream.expect("assign")
            value = parser.parse_expression()
            kwargs.append(nodes.Keyword(key, value, lineno=lineno))
            parser.stream.skip_if("comma")

        func = nodes.Name("_form_render", "load", lineno=lineno)
        args = [nodes.Const(tag, lineno=lineno)]
        call = nodes.Call(func, args, kwargs, None, None, lineno=lineno)
        return nodes.Output([call], lineno=lineno)

    def _auto_name(self, tag: str, kw: dict) -> str:
        if "name" in kw:
            return str(escape(kw["name"]))
        self._counters[tag] = self._counters.get(tag, 0) + 1
        return f"{tag}_{self._counters[tag]}"

    def _render(self, tag, **kw):
        if tag == "checkbox":
            name = self._auto_name(tag, kw)
            if "value" in kw:
                self._prefill[name] = kw["value"]
            return Markup(f'<input type="checkbox" name="{name}" class="inline-cb">')

        if tag == "textfield":
            name = self._auto_name(tag, kw)
            if "value" in kw:
                self._prefill[name] = kw["value"]
            return Markup(f'<input type="text" name="{name}" class="inline-tf">')

        if tag == "textbox":
            name = self._auto_name(tag, kw)
            label = escape(kw.get("label", ""))
            lines = int(kw.get("lines", 3))
            if "value" in kw:
                self._prefill[name] = kw["value"]
            # WeasyPrint doesn't resolve calc() for element height, so express it as one unit
            h = f"{lines * 1.2 + 0.6:.2f}em"
            return Markup(
                f'<div class="tf-block">'
                f'<div class="tf-label">{label}</div>'
                f'<textarea name="{name}" rows="{lines}" class="form-textfield" '
                f'style="height:{h}"></textarea>'
                f'</div>'
            )

        if tag == "signature":
            name = self._auto_name(tag, kw)
            label = escape(kw.get("label", "Signature"))
            height = int(kw.get("height", 60))
            # id="sig_{name}" is the anchor the pdf app looks up via WeasyPrint's Page.anchors
            return Markup(
                f'<div class="sig-block">'
                f'<div class="tf-label">{label}</div>'
                f'<div id="sig_{name}" class="sig-placeholder" style="height:{height}pt">'
                f'<span class="sig-x">&#x2715;</span>'
                f'</div>'
                f'</div>'
            )

        if tag == "vspace":
            lines = int(kw.get("lines", 2))
            height = lines * LINE_H_PT
            return Markup(f'<div style="height:{height}pt"></div>')

        return Markup("")


def _build_env():
    """The general rendering configuration, shared by every template purpose."""
    return SandboxedEnvironment(undefined=StrictUndefined, extensions=[FormFieldExtension], autoescape=False)


def _form_ext(env):
    return next(e for e in env.extensions.values() if isinstance(e, FormFieldExtension))


class ElementDirective(BaseModel):
    """Describes one of the template language's `{% ... %}` form-field tags, in the
    same shape as templates.context_registry.annotate_directives() produces for
    plain data fields, so both can be shown together by the context-schema endpoint."""
    path: str
    type: str = "object"
    directive: str
    description: str


FORM_FIELD_ELEMENTS: list[ElementDirective] = [
    ElementDirective(
        path="checkbox",
        directive="{% checkbox %}",
        description=(
            "Inline checkbox e.g. '{% checkbox %} I agree.' "
        ),
    ),
    ElementDirective(
        path="textfield",
        directive='{% textfield value="<text>" %}',
        description=(
            "Inline single-line text input, underlined, filling the rest of the line. "
            'Optional: value="<text>" to pre-fill'
        ),
    ),
    ElementDirective(
        path="textbox",
        directive='{% textbox label="<label>" lines=<number> value="<text>" %}',
        description=(
            "Labelled multi-line text box block. lines sets its height (default 3). "
            'Optional: value="<text>" to pre-fill'
        ),
    ),
    ElementDirective(
        path="signature",
        directive='{% signature label="<label>" height=<number> %}',
        description=(
            "Signature field. "
            "height is in points (default 60)."
        ),
    ),
    ElementDirective(
        path="vspace",
        directive="{% vspace lines=<number> %}",
        description='Vertical spacing, "lines" amount of lines tall (default 2). Use to separate sections.',
    ),
]


def parse_and_check_context(env, template_str, context):
    """Parse `template_str` with `env` and ensure every referenced variable is in `context`.

    Returns the parsed AST. Raises TemplateRenderError on syntax errors or missing variables.
    """
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

    return ast


def render_from_template(template_str, **context):
    env = _build_env()
    parse_and_check_context(env, template_str, context)

    try:
        return env.from_string(template_str).render(**context)
    except UndefinedError as e:
        raise TemplateRenderError("undefined_variable", str(e))


@dataclass
class WrappedRenderResult:
    """The rendered text (with `prepend`/`append` glued on), plus any AcroForm prefill values."""
    text: str
    prefill: dict = field(default_factory=dict)


def render_with_wrapper(template_str: str, *, prepend: str = "", append: str = "", **context) -> WrappedRenderResult:
    """Render `template_str` with static `prepend`/`append` text glued around it.

    Renders the combined text through the same general Jinja2 configuration as
    `render_from_template`. Callers (e.g. the `pdf` app) supply `prepend`/`append`
    to wrap the template's own content — the templates app has no opinion on
    what that wrapper text contains.
    """
    env = _build_env()
    combined = prepend + template_str + append
    parse_and_check_context(env, combined, context)

    try:
        rendered = env.from_string(combined).render(**context)
    except UndefinedError as e:
        raise TemplateRenderError("undefined_variable", str(e))

    return WrappedRenderResult(text=rendered, prefill=_form_ext(env)._prefill)
