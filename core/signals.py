from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(
    sender, instance: User, created: bool, **kwargs) -> None:
    """
    Signal receiver that creates a UserProfile whenever a new User is created.

    Args:
        sender: The model class (User).
        instance: The actual User instance being saved.
        created: Boolean indicating if this is a new object.
        kwargs: Additional keyword arguments (not used).
    """
    if created:
        UserProfile.objects.create(user=instance)
