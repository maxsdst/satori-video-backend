# Generated by Django 5.0.3 on 2024-04-26 14:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0023_historyentry'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='savedvideo',
            options={'ordering': ['-creation_date']},
        ),
    ]
