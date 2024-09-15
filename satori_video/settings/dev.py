from .common import *


DEBUG = True

SECRET_KEY = "django-insecure-@__74)jxun%=&&y3m^4&(t%1nkbe$)ts6xk6lo0ue2i6i_2$2_"

INSTALLED_APPS = [
    "debug_toolbar",
] + INSTALLED_APPS

# insert debug toolbar middleware after CORS middleware
MIDDLEWARE.insert(
    MIDDLEWARE.index("corsheaders.middleware.CorsMiddleware") + 1,
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

DEBUG_TOOLBAR_ENABLED = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "app",
        "HOST": "postgres",
        "USER": "postgres",
        "PASSWORD": "FireIsComing!",
    }
}

CELERY_BROKER_URL = "redis://redis:6379/1"

GORSE_ENTRY_POINT = "http://gorse_server:8087"
GORSE_API_KEY = ""
