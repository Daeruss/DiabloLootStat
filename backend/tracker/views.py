import logging
from urllib.parse import quote

from django.conf import settings
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

from .models import TelegramProfile, UserState
from .stats import FIELDS, per_boss_totals, totals_for_state
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
        return Response(
            {
                "bot_username": (settings.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@"),
                "bot_id": bot_id,
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


@staff_member_required
def admin_stats(request):
    """Сводка статистики по всем аккаунтам (для персонала)."""
    states = (
        UserState.objects.select_related("user", "user__telegram")
        .order_by("-updated_at")
    )

    def player_name(user):
        tg = getattr(user, "telegram", None)
        if tg:
            return tg.first_name or tg.username or f"tg_{tg.telegram_id}"
        return user.username

    players = []
    global_totals = {f: 0 for f in FIELDS}
    global_totals["splinters"] = 0
    boss_totals = {}

    for st in states:
        t = totals_for_state(st.data)
        players.append(
            {
                "name": player_name(st.user),
                "telegram_id": getattr(getattr(st.user, "telegram", None), "telegram_id", None),
                "totals": t,
                "updated_at": st.updated_at,
            }
        )
        for key in list(FIELDS) + ["splinters"]:
            global_totals[key] += t[key]
        for name, agg in per_boss_totals(st.data).items():
            acc = boss_totals.setdefault(name, {k: 0 for k in list(FIELDS) + ["splinters"]})
            for key in list(FIELDS) + ["splinters"]:
                acc[key] += agg[key]

    bosses = sorted(
        ({"name": n, "totals": v} for n, v in boss_totals.items()),
        key=lambda b: b["totals"]["runs"],
        reverse=True,
    )

    context = {
        "players": players,
        "player_count": len(players),
        "global_totals": global_totals,
        "bosses": bosses,
    }
    return render(request, "tracker/admin_stats.html", context)


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
