from django.apps import AppConfig


class AppointmentConfig(AppConfig):
    name = 'appointments'

    def ready(self):
        import appointments.signals  # noqa
