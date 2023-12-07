from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, LikeViewSet, UploadViewSet, VideoViewSet, ViewViewSet

app_name = "videos"

router = DefaultRouter()
router.register("videos", VideoViewSet, basename="videos")
router.register("uploads", UploadViewSet, basename="uploads")
router.register("views", ViewViewSet, basename="views")
router.register("likes", LikeViewSet, basename="likes")
router.register("comments", CommentViewSet, basename="comments")

urlpatterns = router.urls
