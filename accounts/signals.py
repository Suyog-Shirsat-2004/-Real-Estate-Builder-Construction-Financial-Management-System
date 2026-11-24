"""Keep a profile available for every Django user (including superusers)."""

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            full_name=instance.first_name or instance.username,
            email=instance.email or instance.username,
        )
    elif kwargs.get("update_fields") and "email" in kwargs["update_fields"]:
        profile = getattr(instance, "profile", None)
        if profile and not profile.email:
            profile.email = instance.email
            profile.save(update_fields=["email"])
