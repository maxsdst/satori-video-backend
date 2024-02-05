from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "snapshotpagination.tests"
    label = "snapshotpagination_tests"
