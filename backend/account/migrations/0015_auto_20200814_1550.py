# Generated by Django 3.1 on 2020-08-14 15:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_template_intro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='template',
            name='u_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
