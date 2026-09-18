from django.core.management.base import BaseCommand

from mailing.models import EmailAttachment, EmailDelivery
from mailing.services.sending import cleanup_email_attachment


class Command(BaseCommand):
    help = "Retry cleanup of temporary attachments belonging to sent emails."

    def handle(self, *args, **options):
        attachments = (
            EmailAttachment.objects
            .filter(
                delivery__status=EmailDelivery.Status.SENT,
                cleaned_at__isnull=True,
            )
            .select_related(
                "delivery",
                "source_document",
            )
            .order_by("id")
        )

        cleaned_count = 0
        failed_count = 0

        for attachment in attachments.iterator():
            if cleanup_email_attachment(attachment):
                cleaned_count += 1
            else:
                failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Attachment cleanup finished: "
                f"{cleaned_count} cleaned, "
                f"{failed_count} failed."
            )
        )