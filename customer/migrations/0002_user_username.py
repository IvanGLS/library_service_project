# Generated by Django 4.1.7 on 2023-02-24 11:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("customer", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(max_length=60, null=True),
        ),
    ]
