from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TelegramProfile, UserState
from .telegram_auth import verify_telegram_auth


def profile_payload(user):
    tg = getattr(user, "telegram", None)
    return {
        "telegram_id": tg.telegram_id if tg else None,
        "username": tg.username if tg else None,
        "first_name": tg.first_name if tg else user.first_name,
        "photo_url": tg.photo_url if tg else None,
    }


@method_decorator(ensure_csrf_cookie, name="get")
class ConfigView(APIView):
    """Публичный конфиг для фронтенда + установка csrftoken cookie."""

    def get(self, request):
        return Response(
            {"bot_username": (settings.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@")}
        )


@method_decorator(csrf_exempt, name="dispatch")
class TelegramLoginView(APIView):
    """Вход через Telegram Login Widget. CSRF не нужен — подпись проверяет Telegram."""

    def post(self, request):
        data = request.data
        ok, error = verify_telegram_auth(
            {k: str(v) for k, v in data.items()},
            settings.TELEGRAM_BOT_TOKEN,
            settings.TELEGRAM_AUTH_MAX_AGE,
        )
        if not ok:
            return Response({"detail": error}, status=status.HTTP_401_UNAUTHORIZED)

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
        return Response(profile_payload(user))


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
