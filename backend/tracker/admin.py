from django.contrib import admin

from .models import Boss, TelegramProfile, UserState
from .stats import totals_for_state


@admin.register(Boss)
class BossAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "enabled")
    list_editable = ("order", "enabled")
    search_fields = ("name",)


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
        "myth_seals",
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

    @admin.display(description="Печати")
    def myth_seals(self, obj):
        return totals_for_state(obj.data)["mythSeal"]

    @admin.display(description="Осколки")
    def splinters(self, obj):
        return totals_for_state(obj.data)["splinters"]
