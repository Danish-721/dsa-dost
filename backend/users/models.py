from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default="free"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
