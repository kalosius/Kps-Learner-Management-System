from django.apps import AppConfig


class SchoolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'school'

# register signals
    def ready(self):
        import school.signals