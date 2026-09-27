"""Проверка подписи Telegram Login Widget.

Алгоритм: https://core.telegram.org/widgets/login#checking-authorization
"""
import hashlib
import hmac
import time


def verify_telegram_auth(data: dict, bot_token: str, max_age: int = 86400):
    """Возвращает (ok: bool, error: str|None).

    data — payload от Telegram-виджета (id, first_name, auth_date, hash, ...).
    """
    # обрезаем случайные пробелы/переносы строк из переменной окружения —
    # иначе секретный ключ не совпадёт и подпись всегда будет невалидной
    bot_token = (bot_token or "").strip()
    if not bot_token:
        return False, "На сервере не задан TELEGRAM_BOT_TOKEN"

    received_hash = data.get("hash")
    if not received_hash:
        return False, "Отсутствует hash"

    # строка проверки: все поля кроме hash, отсортированы по ключу, k=v через \n
    pairs = [f"{k}={v}" for k, v in sorted(data.items()) if k != "hash"]
    data_check_string = "\n".join(pairs)

    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return False, "Подпись не совпала"

    try:
        auth_date = int(data.get("auth_date", 0))
    except (TypeError, ValueError):
        return False, "Некорректный auth_date"

    if max_age and (time.time() - auth_date) > max_age:
        return False, "Данные авторизации устарели, войдите заново"

    return True, None
