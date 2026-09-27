import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("telegram_id", models.BigIntegerField(db_index=True, unique=True)),
                ("username", models.CharField(blank=True, max_length=64, null=True)),
                ("first_name", models.CharField(blank=True, default="", max_length=128)),
                ("last_name", models.CharField(blank=True, default="", max_length=128)),
                ("photo_url", models.URLField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_login", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="telegram", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="UserState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="state", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
