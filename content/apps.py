from django.apps import AppConfig


class ContentConfig(AppConfig):
    name = 'content'

    def ready(self):
        from . import signals  