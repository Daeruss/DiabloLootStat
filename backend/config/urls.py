import os

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path

from tracker.views import admin_stats


def spa_index(request):
    """Отдаём index.html собранного Vue-приложения (SPA-fallback)."""
    index_file = os.path.join(settings.FRONTEND_DIST, "index.html")
    if not os.path.exists(index_file):
        raise Http404("frontend build not found")
    return FileResponse(open(index_file, "rb"))


urlpatterns = [
    path("admin/stats/", admin_stats, name="admin-stats"),
    path("admin/", admin.site.urls),
    path("api/", include("tracker.urls")),
]

# Всё остальное (кроме api/admin/static) отдаём SPA — только если фронтенд собран
# в этот же образ. При раздельном деплое (nginx + backend) этим занимается nginx.
if settings.SERVE_FRONTEND:
    urlpatterns += [
        re_path(r"^(?!api/|admin/|static/).*$", spa_index),
    ]
