from django.apps import AppConfig


class CofConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cof'

    def ready(self):
        import cof.signals  # noqa: F401
