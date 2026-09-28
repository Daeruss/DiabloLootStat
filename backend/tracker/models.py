from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    """Данные Telegram-аккаунта, привязанные к пользователю Django."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram",
    )
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=64, blank=True, null=True)
    first_name = models.CharField(max_length=128, blank=True, default="")
    last_name = models.CharField(max_length=128, blank=True, default="")
    photo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name or self.username or self.telegram_id} ({self.telegram_id})"


class Boss(models.Model):
    """Глобальный каталог боссов (общий для всех). Редактируется в админке."""

    name = models.CharField("Имя", max_length=60, unique=True)
    order = models.PositiveIntegerField("Порядок", default=100)
    enabled = models.BooleanField("Показывать", default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Босс"
        verbose_name_plural = "Боссы"

    def __str__(self):
        return self.name


class UserState(models.Model):
    """Вся статистика пользователя одним JSON-документом (боссы × Torment)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="state",
    )
    data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"state of {self.user_id}"
