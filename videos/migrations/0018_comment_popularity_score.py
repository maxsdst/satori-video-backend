# Generated by Django 4.2.3 on 2024-01-04 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0017_comment_mentioned_profile_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='popularity_score',
            field=models.IntegerField(default=0),
        ),
    ]
