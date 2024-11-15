# Generated by Django 5.0.3 on 2024-04-26 14:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_alter_profile_description'),
        ('videos', '0022_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='profiles.profile')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history_entries', to='videos.video')),
            ],
            options={
                'ordering': ['-creation_date'],
            },
        ),
    ]
