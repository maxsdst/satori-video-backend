# Generated by Django 4.2.3 on 2023-07-22 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0006_remove_upload_user_remove_video_user_upload_profile_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='source',
            field=models.FileField(upload_to=''),
        ),
        migrations.AlterField(
            model_name='video',
            name='thumbnail',
            field=models.FileField(upload_to=''),
        ),
    ]
