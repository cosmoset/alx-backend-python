from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    verbose_name = 'Messaging System'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures that signal handlers are registered when Django starts.
        """
        try:
            import messaging.signals
        except ImportError:
            pass