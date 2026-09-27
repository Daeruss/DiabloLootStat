# Diablo 4 — Счётчик дропа боссов

Веб-приложение для учёта статистики дропа боссов в Diablo 4: забеги, мифическое
обмундирование, мифические талисманы и осколки (Splinters) — раздельно по каждому
из 12 уровней Torment. Многопользовательское, с авторизацией через Telegram.

## Стек

- **Frontend:** Vue 3 + Vite, раздаётся через nginx.
- **Backend:** Django + Django REST Framework (gunicorn).
- **БД:** PostgreSQL. Статистика каждого пользователя хранится в модели `UserState`
  (JSON-документ), привязанной к его Telegram-аккаунту.
- **Авторизация:** Telegram Login Widget (подпись проверяется на сервере по HMAC).
- **Запуск:** Docker Compose (`db` + `backend` + `frontend`).

## Структура

```
.
├─ backend/            Django-проект (config) + приложение tracker
├─ frontend/           Vue 3 (Vite) + nginx (отдаёт статику, проксирует /api,/admin,/static)
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

nginx во фронтенд-контейнере отдаёт собранный Vue и проксирует `/api/`, `/admin/`,
`/static/` на backend — всё работает с одного origin, поэтому нет проблем с CORS.

## 1. Создание Telegram-бота

1. В Telegram напишите [@BotFather](https://t.me/BotFather) → `/newbot`, задайте имя и
   username. Скопируйте **токен** и запомните **username** бота.
2. Привяжите домен, на котором будет крутиться сайт (Login Widget работает только с
   привязанного домена и только по HTTPS):
   `/setdomain` → выберите бота → введите домен, например `d4.your-domain.example`.

## 2. Настройка окружения

```bash
cp .env.example .env
```

Заполните `.env`:

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` — из BotFather.
- `DJANGO_SECRET_KEY` — длинная случайная строка.
- `DJANGO_ALLOWED_HOSTS` — ваш домен (+ `localhost` для отладки).
- `DJANGO_CSRF_TRUSTED_ORIGINS` — `https://ваш-домен` (со схемой).
- `DJANGO_COOKIE_SECURE=1` — если раздаёте по HTTPS.
- `POSTGRES_*` — креды базы.
- `APP_PORT` — порт, на котором приложение торчит наружу (по умолчанию 8080).

## 3. Запуск локально

```bash
docker compose up --build
```

Приложение: <http://localhost:8080>. Миграции и `collectstatic` выполняются
автоматически при старте backend.

Создать администратора для Django-админки (`/admin/`):

```bash
docker compose exec backend python manage.py createsuperuser
```

> Для локальной отладки по http Telegram-виджет не заработает (нужен привязанный
> HTTPS-домен). Логику счётчиков можно проверять и без входа, но синхронизация с БД
> требует авторизации.

## 4. Деплой на RelaxDev

⚠️ RelaxDev **не использует `docker-compose`** — он деплоит один контейнер на проект
и ищет `Dockerfile` в корне выбранной папки проекта (`rootDir`). Поэтому для этой
платформы есть **комбинированный `Dockerfile` в корне репозитория**: он собирает
Vue и кладёт его в Django-образ, который сам отдаёт и SPA, и API (одна служба,
один порт). БД подключается отдельным аддоном PostgreSQL через `DATABASE_URL`.

Шаги:

1. **Создайте проект** на RelaxDev, укажите репозиторий и ветку.
2. **rootDir** оставьте корнем репозитория (`/`), а в настройке стека выберите
   «свой Dockerfile» → корневой `Dockerfile`. (Автоопределение тоже подхватит
   корневой Dockerfile.)
3. **Добавьте PostgreSQL** в разделе «База данных» проекта — платформа сама создаст
   базу и переменную `DATABASE_URL`, которую backend уже умеет читать.
4. **Переменные окружения** (шаг «Переменные окружения (.env)»):
   - `DJANGO_SECRET_KEY` — длинная случайная строка;
   - `DJANGO_DEBUG=0`;
   - `DJANGO_ALLOWED_HOSTS` — выданный доменом RelaxDev хост (например
     `myapp.relaxdev.ru`);
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://<этот-домен>`;
   - `DJANGO_COOKIE_SECURE=1`;
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`.
   - `DATABASE_URL` и `PORT` платформа проставляет автоматически — вручную не нужно.
5. **Привяжите домен в BotFather** (`/setdomain`) — тот же, что выдал RelaxDev.
6. Задеплойте. HTTPS платформа терминирует сама; `SECURE_PROXY_SSL_HEADER` уже
   включается при `DJANGO_DEBUG=0`.

Суперпользователь для админки — через веб-консоль/шелл проекта на RelaxDev:
`python manage.py createsuperuser`.

> **Альтернатива (два проекта).** Можно деплоить `backend/` и `frontend/` как
> отдельные проекты RelaxDev (у каждого свой `rootDir` и свой `Dockerfile`). Но тогда
> nginx фронтенда придётся проксировать `/api` на публичный домен бэкенда, и нужно
> аккуратно настроить общий домен для cookie. Комбинированный образ проще — рекомендую его.

## Локальный запуск (docker-compose) vs RelaxDev

- **Локально** удобнее `docker compose up` — там 3 контейнера (db + backend + nginx-фронт),
  фронт проксирует `/api` на backend по имени сервиса.
- **На RelaxDev** используется корневой `Dockerfile` — один контейнер, Django отдаёт всё сам.

Оба варианта работают с одним и тем же кодом.

## Разработка без Docker

Backend:

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# поднимите Postgres и укажите POSTGRES_* в окружении
python manage.py migrate
python manage.py runserver
```

Frontend (Vite проксирует /api на localhost:8000):

```bash
cd frontend
npm install
npm run dev
```

Открыть <http://localhost:5173>.

## API

| Метод | Путь                  | Назначение                                  |
|-------|-----------------------|---------------------------------------------|
| GET   | `/api/config/`        | username бота + установка csrftoken cookie  |
| POST  | `/api/auth/telegram/` | вход по данным Telegram Login Widget         |
| POST  | `/api/auth/logout/`   | выход                                        |
| GET   | `/api/me/`            | текущий пользователь (401 если не вошёл)     |
| GET   | `/api/state/`         | статистика пользователя                      |
| PUT   | `/api/state/`         | сохранить статистику (`{ "data": {...} }`)   |
