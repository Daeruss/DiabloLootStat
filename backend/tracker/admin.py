from django.contrib import admin

from .models import Boss, Season, TelegramProfile, UserState
from .stats import get_bosses, totals_for_bosses


def _current_season():
    s = Season.objects.filter(is_current=True).values_list("number", flat=True).first()
    if s is not None:
        return s
    s = Season.objects.order_by("-number").values_list("number", flat=True).first()
    return s if s is not None else 15


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "is_current")
    list_editable = ("title", "is_current")
    ordering = ("-number",)


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

    def _totals(self, obj):
        return totals_for_bosses(get_bosses(obj.data, _current_season()))

    @admin.display(description="Забеги")
    def runs(self, obj):
        return self._totals(obj)["runs"]

    @admin.display(description="Мифики")
    def myth(self, obj):
        return self._totals(obj)["myth"]

    @admin.display(description="Талисманы")
    def myth_talismans(self, obj):
        return self._totals(obj)["mythTal"]

    @admin.display(description="Печати")
    def myth_seals(self, obj):
        return self._totals(obj)["mythSeal"]

    @admin.display(description="Осколки")
    def splinters(self, obj):
        return self._totals(obj)["splinters"]
