from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "custompagination.tests"
    label = "custompagination_tests"
