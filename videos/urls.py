from rest_framework.routers import DefaultRouter

from .views import LikeViewSet, UploadViewSet, VideoViewSet, ViewViewSet


app_name = "videos"

router = DefaultRouter()
router.register("videos", VideoViewSet, basename="videos")
router.register("uploads", UploadViewSet, basename="uploads")
router.register("views", ViewViewSet, basename="views")
router.register("likes", LikeViewSet, basename="likes")

urlpatterns = router.urls
