from django.db.models.signals import post_delete
from django.dispatch import receiver

from appointments.models import Appointment
from documents.models import Document


@receiver(post_delete, sender=Appointment)
def delete_appointment_minutes(sender, instance, **kwargs):
    """An Appointment's minutes Document has no reason to exist once the appointment is gone."""
    if instance.minutes_id is not None:
        Document.objects.filter(pk=instance.minutes_id).delete()
