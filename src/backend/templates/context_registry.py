"""
Registry mapping each Purpose to its Pydantic context class.

The context class is the single source of truth for:
  - what variables a template for that purpose can reference
  - how to build the context from request-supplied IDs at render time

Each entry is a subclass of BaseModel with a `build(**kwargs)` classmethod.
"""
from pydantic import BaseModel

from counselors.models import Counselor
from counselors.template_context import CounselorContext, AllAvailableSlotsContext
from students.template_context import StudentContext
from students.models import Student
from templates.models import Purpose
from appointments.appointment_context import AppointmentContext
from appointments.models import Appointment





class TestmailContext(BaseModel):
    counselor: CounselorContext
    
    @classmethod
    def build(cls, counselor_id: int) -> "TestmailContext":
        counselor = Counselor.objects.get(id=counselor_id)
        return cls(counselor=CounselorContext.from_model(counselor))


class StudentAndBlocksContext(BaseModel):
    available_slots: AllAvailableSlotsContext
    student: StudentContext

    @classmethod
    def build(cls,student_id: int) -> "StudentAndBlocksContext":
        available_slots = AllAvailableSlotsContext.build()
        student = StudentContext.from_model(Student.objects.get(id=student_id))
        return cls(available_slots=available_slots, student=student)



class AppointmentStudentCounselorContext(BaseModel):
    student: StudentContext
    counselor: CounselorContext
    appointment: AppointmentContext

    @classmethod
    def build(cls, student_id: int, counselor_id: int, appointment_id: int) -> "AppointmentStudentCounselorContext":
        student = StudentContext.from_model(Student.objects.get(id=student_id))
        counselor = CounselorContext.from_model(Counselor.objects.get(id=counselor_id))
        appointment = AppointmentContext.from_model(Appointment.objects.get(id=appointment_id))
        return cls(student=student, counselor=counselor, appointment=appointment)


class PDFContext(BaseModel):
    """Mixin for purpose contexts rendered as a PDF. Subclassing this is what makes
    purpose_context_schema include the form-field element directives (see
    templates.rendering.FORM_FIELD_ELEMENTS) alongside the plain data fields."""
    pass


class StudyPlanContext(PDFContext):
    student: StudentContext

    @classmethod
    def build(cls, student_id: int) -> "StudyPlanContext":
        student = StudentContext.from_model(Student.objects.get(id=student_id))
        return cls(student=student)
    
    
class AppointmentMinutesContext(PDFContext):
    student: StudentContext
    counselor: CounselorContext
    appointment: AppointmentContext

    @classmethod
    def build(cls, student_id: int, counselor_id: int, appointment_id: int) -> "AppointmentMinutesContext":
        student = StudentContext.from_model(Student.objects.get(id=student_id))
        counselor = CounselorContext.from_model(Counselor.objects.get(id=counselor_id))
        appointment = AppointmentContext.from_model(Appointment.objects.get(id=appointment_id))
        return cls(student=student, counselor=counselor, appointment=appointment)

    




# ── Registry ────────────────────────────────────────────────────────────────
# Add one entry here for every new Purpose value.
PURPOSE_CONTEXT_REGISTRY: dict[str, type[BaseModel]] = {
    Purpose.TESTMAIL: TestmailContext,
    Purpose.STUDENT_INVITATION_MAIL: StudentAndBlocksContext,
    Purpose.STUDENT_REMINDER_MAIL: StudentAndBlocksContext,
    Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL: AppointmentStudentCounselorContext,
    Purpose.APPOINTMENT_INVITATION_MAIL: AppointmentStudentCounselorContext,
    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL: AppointmentStudentCounselorContext,
    Purpose.APPOINTMENT_CANCELLATION_MAIL: AppointmentStudentCounselorContext,
    Purpose.STUDY_PLAN: StudyPlanContext,
    Purpose.APPOINTMENT_MINUTES: AppointmentMinutesContext,
}







def flatten_context_schema(schema: dict) -> list[dict]:
    """
    Convert a Pydantic model_json_schema() dict into a flat list of
    { path, type } entries suitable for a template editor.

    - Intermediate objects are NOT emitted — only their leaf fields.
    - Arrays ARE emitted (so the author knows they can loop), plus each
      field of the array item is emitted as  path[].field_name.
    - `format` (e.g. "date", "time") is preferred over `type` when present.
    """
    defs = schema.get("$defs", {})

    def resolve(node: dict) -> dict:
        if "$ref" in node:
            return defs[node["$ref"].split("/")[-1]]
        return node

    result: list[dict] = []

    def walk(node: dict, prefix: str) -> None:
        for field_name, raw in node.get("properties", {}).items():
            field = resolve(raw)
            path = f"{prefix}.{field_name}" if prefix else field_name
            field_type = field.get("type")

            if field_type == "object":
                walk(field, path)
            elif field_type == "array":
                result.append({"path": path, "type": "array"})
                items = resolve(field.get("items", {}))
                if items.get("type") == "object":
                    walk(items, f"{path}[]")
            else:
                result.append({"path": path, "type": field.get("format") or field_type or "unknown"})

    walk(schema, "")
    return result


def _singularize(name: str) -> str:
    """Strip a trailing 's' to derive a simple loop-variable name (e.g. 'slots' -> 'slot')."""
    return name[:-1] if name.endswith("s") else name


def annotate_directives(flat: list[dict]) -> list[dict]:
    """
    Enrich each entry from flatten_context_schema() with:
      - 'directive'  : ready-to-paste template directive
      - 'description': human-readable placement instruction

    Three cases:
      List              (type == "array")    -> {% for elem in path %} … {% endfor %}
      List Element var  ("[]" in path)       -> {{elem.sub_path}}
      Classical         (plain scalar leaf)  -> {{path}}
    """
    result = []
    for entry in flat:
        path: str = entry["path"]
        field_type: str = entry["type"]
        new_entry = {**entry}

        if field_type == "array":
            list_name = path.rsplit(".", 1)[-1]
            elem_var = _singularize(list_name)
            new_entry["directive"] = f"{{% for {elem_var} in {path} %}}\n\n{{% endfor %}}"
            new_entry["description"] = "Place to iterate over the List"

        elif "[]" in path:
            bracket_idx = path.index("[]")
            list_prefix = path[:bracket_idx]
            suffix = path[bracket_idx + 2:]          # e.g. ".start_time"
            list_name = list_prefix.rsplit(".", 1)[-1]
            elem_var = _singularize(list_name)
            modified = elem_var + suffix
            new_entry["directive"] = "{{" + modified + "}}"
            new_entry["description"] = (
                f"To be placed INSIDE a loop over {list_name}. Will be replaced by the actual value."
            )

        else:
            new_entry["directive"] = "{{" + path + "}}"
            new_entry["description"] = "Can be placed to be replaced by the actual value."

        result.append(new_entry)
    return result

