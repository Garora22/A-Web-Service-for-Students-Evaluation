from django.db.models.signals import post_save
from django.dispatch import receiver

from .extract import extract_and_cache_material_text
from .models import CourseMaterial


@receiver(post_save, sender=CourseMaterial)
def cache_material_text_on_upload(sender, instance: CourseMaterial, created: bool, **kwargs):
    if instance.file:
        extract_and_cache_material_text(instance)

