from django.apps import AppConfig

class CertificatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'certificates'

    def ready(self):
        """
        Connects the signal handlers in certificates.signals when the app is loaded.
        """
        import certificates.signals