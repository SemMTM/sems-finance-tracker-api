# Generated by Django 5.1.7 on 2025-05-26 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0010_alter_disposableincomebudget_amount_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disposableincomespending',
            name='title',
            field=models.CharField(help_text='Short description of the expenditure.', max_length=100),
        ),
        migrations.AlterField(
            model_name='expenditure',
            name='title',
            field=models.CharField(help_text='Name or label for this expenditure.', max_length=100),
        ),
        migrations.AlterField(
            model_name='income',
            name='title',
            field=models.CharField(help_text='Short label for this income source.', max_length=100),
        ),
    ]
