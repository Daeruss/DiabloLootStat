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


class Season(models.Model):
    """Сезон Diablo 4. Статистика ведётся отдельно по каждому сезону."""

    number = models.PositiveIntegerField("Номер", unique=True)
    title = models.CharField("Название", max_length=80, blank=True, default="")
    is_current = models.BooleanField("Текущий", default=False)

    class Meta:
        ordering = ["-number"]
        verbose_name = "Сезон"
        verbose_name_plural = "Сезоны"

    def __str__(self):
        return self.title or f"Сезон {self.number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # текущий сезон может быть только один
        if self.is_current:
            Season.objects.exclude(pk=self.pk).filter(is_current=True).update(
                is_current=False
            )


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
