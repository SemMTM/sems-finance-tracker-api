# Generated by Django 5.1.7 on 2025-04-01 13:18

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_alter_disposableincomebudget_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='disposableincomebudget',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
