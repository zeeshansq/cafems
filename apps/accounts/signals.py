"""Accounts App – Signals."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def sync_username_with_email(sender, instance, created, **kwargs):
    """Keep username in sync with email (since we use email as USERNAME_FIELD)."""
    if instance.username != instance.email:
        User.objects.filter(pk=instance.pk).update(username=instance.email)
