# Generated by Django 5.1.7 on 2025-04-29 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0005_expenditure_repeat_group_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='income',
            name='repeat_group_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
    ]
