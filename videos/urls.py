from rest_framework.routers import DefaultRouter

from .views import UploadViewSet, VideoViewSet


app_name = "videos"

router = DefaultRouter()
router.register("videos", VideoViewSet, basename="videos")
router.register("uploads", UploadViewSet, basename="uploads")

urlpatterns = router.urls
