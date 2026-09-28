import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Boss, Season, TelegramProfile, UserState
from .stats import (
    TORMENT_KEYS,
    TORMENT_OPTIONS,
    all_season_keys,
    collect_boss_names,
    get_bosses,
    is_empty,
    merge_boss_into,
    per_boss_filtered,
    totals_filtered,
    with_rates,
)


def current_season_number():
    """Номер текущего сезона (или самый большой, или 15 по умолчанию)."""
    s = Season.objects.filter(is_current=True).values_list("number", flat=True).first()
    if s is not None:
        return s
    s = Season.objects.order_by("-number").values_list("number", flat=True).first()
    return s if s is not None else 15
from .telegram_auth import verify_telegram_auth

logger = logging.getLogger("tracker.auth")


def profile_payload(user):
    tg = getattr(user, "telegram", None)
    return {
        "telegram_id": tg.telegram_id if tg else None,
        "username": tg.username if tg else None,
        "first_name": tg.first_name if tg else user.first_name,
        "photo_url": tg.photo_url if tg else None,
    }


def upsert_and_login(request, data):
    """Создаёт/обновляет Telegram-профиль по проверенным данным и логинит сессию."""
    telegram_id = int(data["id"])
    profile = TelegramProfile.objects.filter(telegram_id=telegram_id).first()
    if profile:
        user = profile.user
    else:
        user = User.objects.create(username=f"tg_{telegram_id}")
        profile = TelegramProfile(user=user, telegram_id=telegram_id)

    profile.username = data.get("username") or None
    profile.first_name = data.get("first_name") or ""
    profile.last_name = data.get("last_name") or ""
    profile.photo_url = data.get("photo_url") or None
    profile.save()

    login(request, user)
    return user


def _log_reject(where, error):
    logger.warning(
        "Telegram %s rejected: %s | token_len=%s",
        where,
        error,
        len((settings.TELEGRAM_BOT_TOKEN or "").strip()),
    )


@method_decorator(ensure_csrf_cookie, name="get")
class ConfigView(APIView):
    """Публичный конфиг для фронтенда + установка csrftoken cookie."""

    def get(self, request):
        token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
        bot_id = token.split(":")[0] if ":" in token else ""
        bosses = list(
            Boss.objects.filter(enabled=True).values_list("name", flat=True)
        )
        seasons = list(Season.objects.values_list("number", flat=True))
        return Response(
            {
                "bot_username": (settings.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@"),
                "bot_id": bot_id,
                "bosses": bosses,
                "season": current_season_number(),
                "seasons": seasons,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class TelegramLoginView(APIView):
    """Вход через Telegram Login Widget (callback-режим, POST с JSON).

    CSRF не нужен — подлинность подтверждает подпись Telegram."""

    def post(self, request):
        data = {k: str(v) for k, v in request.data.items()}
        ok, error = verify_telegram_auth(
            dict(data), settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_AUTH_MAX_AGE
        )
        if not ok:
            _log_reject("auth (POST)", error)
            return Response({"detail": error}, status=status.HTTP_401_UNAUTHORIZED)

        user = upsert_and_login(request, data)
        return Response(profile_payload(user))


class TelegramRedirectView(APIView):
    """Вход через Telegram Login Widget (redirect-режим, GET с query-параметрами).

    Надёжнее callback-режима в SPA: Telegram сам делает top-level переход сюда,
    мы проверяем подпись, ставим сессию и возвращаем пользователя на главную."""

    def get(self, request):
        data = {k: str(v) for k, v in request.query_params.items()}
        ok, error = verify_telegram_auth(
            dict(data), settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_AUTH_MAX_AGE
        )
        if not ok:
            _log_reject("auth (redirect)", error)
            return redirect("/?auth_error=" + quote(error or "auth failed"))

        upsert_and_login(request, data)
        return redirect("/")


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


SUM_KEYS = [
    "runs",
    "myth",
    "mythTal",
    "mythSeal",
    "splBaal",
    "splMeph",
    "splDiablo",
    "splinters",
]


def _player_name(user):
    tg = getattr(user, "telegram", None)
    if tg:
        return tg.first_name or tg.username or f"tg_{tg.telegram_id}"
    return user.username


@staff_member_required
def admin_stats(request):
    """Сводка статистики по всем аккаунтам с фильтрами (для персонала)."""
    states = list(
        UserState.objects.select_related("user", "user__telegram").order_by("-updated_at")
    )

    all_seasons = list(Season.objects.values_list("number", flat=True))
    # выбранный сезон (по умолчанию текущий)
    try:
        season = int(request.GET.get("season", current_season_number()))
    except (TypeError, ValueError):
        season = current_season_number()
    if all_seasons and season not in all_seasons:
        season = current_season_number()

    all_bosses = collect_boss_names(states, season)

    # фильтры из query-строки
    torment = request.GET.get("torment", "all")
    boss = request.GET.get("boss", "all")
    sort = request.GET.get("sort", "runs")
    t_filter = torment if torment in TORMENT_KEYS else None
    b_filter = boss if boss in all_bosses else None
    if sort not in SUM_KEYS:
        sort = "runs"

    players = []
    global_totals = {k: 0 for k in SUM_KEYS}
    boss_totals = {}

    for st in states:
        bosses_data = get_bosses(st.data, season)
        t = totals_filtered(bosses_data, t_filter, b_filter)
        for key in SUM_KEYS:
            global_totals[key] += t[key]
        if not is_empty(t):
            players.append(
                {
                    "name": _player_name(st.user),
                    "telegram_id": getattr(
                        getattr(st.user, "telegram", None), "telegram_id", None
                    ),
                    "totals": with_rates(t),
                    "updated_at": st.updated_at,
                }
            )
        for name, agg in per_boss_filtered(bosses_data, t_filter).items():
            if b_filter and name != b_filter:
                continue
            acc = boss_totals.setdefault(name, {k: 0 for k in SUM_KEYS})
            for key in SUM_KEYS:
                acc[key] += agg[key]

    players.sort(key=lambda p: p["totals"].get(sort, 0), reverse=True)
    bosses = sorted(
        ({"name": n, "totals": with_rates(v)} for n, v in boss_totals.items()),
        key=lambda b: b["totals"].get(sort, 0),
        reverse=True,
    )

    context = {
        "players": players,
        "player_count": len(players),
        "total_accounts": len(states),
        "global_totals": with_rates(global_totals),
        "bosses": bosses,
        "torment_options": TORMENT_OPTIONS,
        "boss_options": all_bosses,
        "season_options": all_seasons,
        "sel_season": season,
        "sel_torment": torment,
        "sel_boss": boss if b_filter else "all",
        "sel_sort": sort,
    }
    return render(request, "tracker/admin_stats.html", context)


@staff_member_required
def merge_bosses(request):
    """Объединение статистики: переносит всё с босса-источника на босса-приёмник
    во всех аккаунтах (в JSON каждого пользователя)."""
    bosses = list(Boss.objects.all())

    if request.method == "POST":
        src = (request.POST.get("source") or "").strip()
        dst = (request.POST.get("target") or "").strip()
        delete_source = request.POST.get("delete_source") == "on"

        if not src or not dst or src == dst:
            messages.error(request, "Выберите двух разных боссов.")
            return redirect("merge-bosses")

        affected = 0
        for st in UserState.objects.all():
            data = st.data or {}
            seasons = data.get("seasons")
            changed = False
            # объединяем во всех сезонах игрока
            if isinstance(seasons, dict):
                for skey, sdata in seasons.items():
                    bosses_data = (sdata or {}).get("bosses") or {}
                    if merge_boss_into(bosses_data, src, dst):
                        del bosses_data[src]
                        sdata["bosses"] = bosses_data
                        changed = True
            else:
                # legacy плоская структура (на случай, если не мигрировано)
                bosses_data = data.get("bosses") or {}
                if merge_boss_into(bosses_data, src, dst):
                    del bosses_data[src]
                    data["bosses"] = bosses_data
                    changed = True
            if changed:
                if data.get("current") == src:
                    data["current"] = dst
                st.data = data
                st.save(update_fields=["data", "updated_at"])
                affected += 1

        if delete_source:
            Boss.objects.filter(name=src).delete()

        messages.success(
            request,
            f"Готово: «{src}» → «{dst}». Обновлено аккаунтов: {affected}."
            + (" Босс-источник удалён из каталога." if delete_source else ""),
        )
        return redirect("merge-bosses")

    return render(request, "tracker/merge_bosses.html", {"bosses": bosses})


@method_decorator(ensure_csrf_cookie, name="get")
class MeView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Не авторизован"}, status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(profile_payload(request.user))


class StateView(APIView):
    """Чтение/запись всей статистики пользователя (JSON-документ)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        obj = UserState.objects.filter(user=request.user).first()
        return Response({"data": obj.data if obj else {}})

    def put(self, request):
        data = request.data.get("data")
        if not isinstance(data, dict):
            return Response(
                {"detail": "Ожидается объект data"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        UserState.objects.update_or_create(
            user=request.user, defaults={"data": data}
        )
        return Response({"ok": True})
