# Generated by Django 3.1 on 2020-08-11 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_edithistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='u_avatar',
            field=models.ImageField(default='Avatar/default_avatar.jpg', upload_to='Avatar/'),
        ),
    ]
