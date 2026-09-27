from django.contrib import admin

from .models import TelegramProfile, UserState
from .stats import totals_for_state


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "first_name", "created_at", "last_login")
    search_fields = ("telegram_id", "username", "first_name")


@admin.register(UserState)
class UserStateAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "runs",
        "myth",
        "myth_talismans",
        "splinters",
        "updated_at",
    )
    readonly_fields = ("updated_at",)

    @admin.display(description="Игрок")
    def player(self, obj):
        tg = getattr(obj.user, "telegram", None)
        if tg:
            return tg.first_name or tg.username or f"tg_{tg.telegram_id}"
        return obj.user.username

    @admin.display(description="Забеги")
    def runs(self, obj):
        return totals_for_state(obj.data)["runs"]

    @admin.display(description="Мифики")
    def myth(self, obj):
        return totals_for_state(obj.data)["myth"]

    @admin.display(description="Талисманы")
    def myth_talismans(self, obj):
        return totals_for_state(obj.data)["mythTal"]

    @admin.display(description="Осколки")
    def splinters(self, obj):
        return totals_for_state(obj.data)["splinters"]
