from django.db import models


class Snapshot(models.Model):
    primary_keys = models.JSONField()
    creation_date = models.DateTimeField(auto_now_add=True)
