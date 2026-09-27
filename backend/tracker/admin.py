from django.contrib import admin

from .models import TelegramProfile, UserState


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "first_name", "created_at", "last_login")
    search_fields = ("telegram_id", "username", "first_name")


@admin.register(UserState)
class UserStateAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
