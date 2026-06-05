"""
Registry mapping each Purpose to its Pydantic context class.

The context class is the single source of truth for:
  - what variables a template for that purpose can reference
  - how to build the context from request-supplied IDs at render time

Each entry is a subclass of BaseModel with a `build(**kwargs)` classmethod.
"""
from pydantic import BaseModel

from counselors.models import Counselor
from counselors.template_context import CounselorContext, AllAvailableBlocksContext
from students.template_context import StudentContext
from students.models import Student
from templates.models import Purpose






class TestmailContext(BaseModel):
    counselor: CounselorContext
    
    @classmethod
    def build(cls, counselor_id: int) -> "TestmailContext":
        counselor = Counselor.objects.get(id=counselor_id)
        return cls(counselor=CounselorContext.from_model(counselor))


class StudentAndBlocksContext(BaseModel):
    available_blocks: AllAvailableBlocksContext
    student: StudentContext

    @classmethod
    def build(cls,student_id: int) -> "StudentAndBlocksContext":
        available_blocks = AllAvailableBlocksContext.build()
        student = StudentContext.from_model(Student.objects.get(id=student_id))
        return cls(available_blocks=available_blocks, student=student)



class SessionStudentCounselorContext(BaseModel):
    student: StudentContext
    counselor: CounselorContext
    # session: TODO

    @classmethod
    def build(cls, student_id: int, counselor_id: int) -> "SessionStudentCounselorContext":
        student = StudentContext.from_model(Student.objects.get(id=student_id))
        counselor = CounselorContext.from_model(Counselor.objects.get(id=counselor_id))
        #TODO session
        return cls(student=student, counselor=counselor)


class StudyPlanContext(BaseModel):
    student: StudentContext
    # elements: TODO
    
    @classmethod
    def build(cls, student_id: int) -> "StudyPlanContext":
        raise NotImplementedError("StudyPlanContext.build is not implemented yet")
    
    
class SessionMinutesContext(BaseModel):
    student: StudentContext
    counselor: CounselorContext
    # session: TODO
    # minutes_elements: TODO
    
    @classmethod
    def build(cls, student_id: int, counselor_id: int) -> "SessionMinutesContext":
        raise NotImplementedError("SessionMinutesContext.build is not implemented yet")

    




# ── Registry ────────────────────────────────────────────────────────────────
# Add one entry here for every new Purpose value.
PURPOSE_CONTEXT_REGISTRY: dict[str, type[BaseModel]] = {
    Purpose.TESTMAIL: TestmailContext,
    Purpose.STUDENT_INVITATION_MAIL: StudentAndBlocksContext,
    Purpose.STUDENT_REMINDER_MAIL: StudentAndBlocksContext,
    Purpose.FORCED_APPOINTMENT_ASSIGNMENT_MAIL: SessionStudentCounselorContext,
    Purpose.SESSION_INVITATION_MAIL: SessionStudentCounselorContext,
    Purpose.COUNSELOR_PREPARATION_INSTRUCTION_MAIL: SessionStudentCounselorContext,
    Purpose.SESSION_CANCELLATION_MAIL: SessionStudentCounselorContext,
    Purpose.STUDY_PLAN: StudyPlanContext,
    Purpose.SESSION_MINUTES: SessionMinutesContext,
}







def flatten_context_schema(schema: dict) -> list[dict]:
    """
    Convert a Pydantic model_json_schema() dict into a flat list of
    { path, type, ?description } entries suitable for a template editor.

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
            description = field.get("description")

            base: dict = {"path": path, "type": field.get("format") or field_type or "unknown"}
            if description:
                base["description"] = description

            if field_type == "object":
                walk(field, path)
            elif field_type == "array":
                result.append({"path": path, "type": "array", **({"description": description} if description else {})})
                items = resolve(field.get("items", {}))
                if items.get("type") == "object":
                    walk(items, f"{path}[]")
            else:
                result.append(base)

    walk(schema, "")
    return result

