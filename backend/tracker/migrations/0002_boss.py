from django.db import migrations, models

DEFAULT_BOSSES = [
    "Дурьель",
    "Андариэль",
    "Варшан",
    "Григоль",
    "Зир",
    "Белиал",
    "Мефисто",
    "Баал",
    "Диабло",
]


def seed_bosses(apps, schema_editor):
    Boss = apps.get_model("tracker", "Boss")
    for i, name in enumerate(DEFAULT_BOSSES, start=1):
        Boss.objects.get_or_create(name=name, defaults={"order": i * 10})


def unseed_bosses(apps, schema_editor):
    Boss = apps.get_model("tracker", "Boss")
    Boss.objects.filter(name__in=DEFAULT_BOSSES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Boss",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60, unique=True, verbose_name="Имя")),
                ("order", models.PositiveIntegerField(default=100, verbose_name="Порядок")),
                ("enabled", models.BooleanField(default=True, verbose_name="Показывать")),
            ],
            options={
                "verbose_name": "Босс",
                "verbose_name_plural": "Боссы",
                "ordering": ["order", "name"],
            },
        ),
        migrations.RunPython(seed_bosses, unseed_bosses),
    ]
