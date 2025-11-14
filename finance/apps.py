from django.apps import AppConfig

class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance'

    def ready(self):
        """
        Connects the signal handlers in finance.signals when the app is loaded.
        """
        import finance.signals