from django.urls import path

from . import views

urlpatterns = [
    path("config/", views.ConfigView.as_view()),
    path("auth/telegram/", views.TelegramLoginView.as_view()),
    path("auth/telegram/redirect/", views.TelegramRedirectView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("me/", views.MeView.as_view()),
    path("state/", views.StateView.as_view()),
]
