"""
Registry mapping each Purpose to its Pydantic context class.

The context class is the single source of truth for:
  - what variables a template for that purpose can reference
  - how to build the context from request-supplied IDs at render time

Each entry is a subclass of BaseModel with a `build(**kwargs)` classmethod.
"""
from pydantic import BaseModel

from counselors.models import Counselor
from counselors.template_context import CounselorContext
from templates.models import Purpose


class TestmailContext(BaseModel):
    counselor: CounselorContext
    
    @classmethod
    def build(cls, counselor_id: int) -> "TestmailContext":
        counselor = Counselor.objects.get(id=counselor_id)
        return cls(counselor=CounselorContext.from_model(counselor))


# ── Registry ────────────────────────────────────────────────────────────────
# Add one entry here for every new Purpose value.
PURPOSE_CONTEXT_REGISTRY: dict[str, type[BaseModel]] = {
    Purpose.TESTMAIL: TestmailContext,
}
