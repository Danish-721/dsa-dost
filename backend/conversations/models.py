from django.contrib.auth.models import User
from django.db import models


class Conversation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations"
    )

    title = models.CharField(
        max_length=200,
        default="New Chat"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Message(models.Model):

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    content = models.TextField()

    model_used = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    fallback_used = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role} - {self.conversation.title}"