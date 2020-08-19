# Generated by Django 3.0.5 on 2020-08-19 15:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_team_intro'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='m_type',
            new_name='m_title',
        ),
        migrations.AddField(
            model_name='message',
            name='file',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='msg_file', to='account.File'),
        ),
        migrations.AddField(
            model_name='message',
            name='team',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.DO_NOTHING, related_name='msg_team', to='account.Team'),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='first name'),
        ),
    ]