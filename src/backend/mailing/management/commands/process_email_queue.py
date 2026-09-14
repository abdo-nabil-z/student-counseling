import time

from django.conf import settings
from django.core.management.base import BaseCommand

from mailing.services.processing import process_next_queued_delivery


class Command(BaseCommand):
    help = "Process queued email deliveries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process at most one ready email and then exit."
        )

    def handle(self, *args, **options):
        if options["once"]:
            self._process_once()
            return

        self.stdout.write(
            self.style.SUCCESS("Email queue worker started.")
        )

        self.stdout.write(
            (
                "Send interval: "
                f"{settings.EMAIL_SEND_INTERVAL_SECONDS} "
                "seconds"
            )
        )

        try:
            while True:
                processed = process_next_queued_delivery()

                if processed:
                    time.sleep(settings.EMAIL_SEND_INTERVAL_SECONDS)

                else:
                    time.sleep(settings.EMAIL_QUEUE_POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            self.stdout.write("")

            self.stdout.write(
                self.style.WARNING(
                    "Email queue worker stopped."
                )
            )


    def _process_once(self):
        processed = process_next_queued_delivery()

        if processed:
            self.stdout.write(
                self.style.SUCCESS("Processed one email delivery.")
            )

        else:
            self.stdout.write("No queued email is ready.")