# Generated by Django 3.1 on 2020-08-13 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_auto_20200813_0901'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='edit_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='template',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
