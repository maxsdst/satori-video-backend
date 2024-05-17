from django.conf import settings
from django.db import models


class Notification(models.Model):
    @property
    def type(self):
        raise NotImplementedError

    @property
    def subtype(self):
        raise NotImplementedError

    profile = models.ForeignKey(
        settings.PROFILE_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)
    seen_date = models.DateTimeField(null=True, default=None)
