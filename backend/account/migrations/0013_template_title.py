# Generated by Django 3.1 on 2020-08-14 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_auto_20200814_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='title',
            field=models.CharField(default='default_template', max_length=20),
            preserve_default=False,
        ),
    ]
