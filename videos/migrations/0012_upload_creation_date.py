# Generated by Django 4.2.3 on 2023-10-27 18:12

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0011_upload_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='upload',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]