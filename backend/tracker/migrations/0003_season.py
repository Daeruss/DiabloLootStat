from django.db import migrations, models

CURRENT_SEASON = 15


def seed_and_restructure(apps, schema_editor):
    Season = apps.get_model("tracker", "Season")
    UserState = apps.get_model("tracker", "UserState")

    Season.objects.get_or_create(
        number=CURRENT_SEASON, defaults={"is_current": True}
    )

    # переносим существующую «плоскую» статистику в текущий сезон
    key = str(CURRENT_SEASON)
    for st in UserState.objects.all():
        data = st.data
        if not isinstance(data, dict):
            continue
        if "bosses" in data and "seasons" not in data:
            bosses = data.pop("bosses")
            data["seasons"] = {key: {"bosses": bosses}}
            st.data = data
            st.save(update_fields=["data"])


def reverse(apps, schema_editor):
    Season = apps.get_model("tracker", "Season")
    UserState = apps.get_model("tracker", "UserState")
    key = str(CURRENT_SEASON)
    for st in UserState.objects.all():
        data = st.data
        if isinstance(data, dict) and "seasons" in data:
            seasons = data.pop("seasons")
            season = seasons.get(key) or {}
            data["bosses"] = season.get("bosses") or {}
            st.data = data
            st.save(update_fields=["data"])
    Season.objects.filter(number=CURRENT_SEASON).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0002_boss"),
    ]

    operations = [
        migrations.CreateModel(
            name="Season",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveIntegerField(unique=True, verbose_name="Номер")),
                ("title", models.CharField(blank=True, default="", max_length=80, verbose_name="Название")),
                ("is_current", models.BooleanField(default=False, verbose_name="Текущий")),
            ],
            options={
                "verbose_name": "Сезон",
                "verbose_name_plural": "Сезоны",
                "ordering": ["-number"],
            },
        ),
        migrations.RunPython(seed_and_restructure, reverse),
    ]
