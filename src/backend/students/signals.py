from django.db.models.signals import post_delete
from django.dispatch import receiver

from documents.models import Document
from students.models import Student


@receiver(post_delete, sender=Student)
def delete_student_documents(sender, instance, **kwargs):
    """A Student's attached Documents have no reason to exist once the student is gone."""
    document_ids = {
        instance.initial_study_plan_id,
        instance.final_study_plan_id,
    }

    for document_id in document_ids:
        if document_id is not None:
            Document.objects.filter(pk=document_id).delete()
