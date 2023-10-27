# Generated by Django 4.2.3 on 2023-10-06 00:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0009_alter_video_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='upload_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]