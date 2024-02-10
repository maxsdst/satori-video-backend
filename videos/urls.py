from rest_framework.routers import DefaultRouter

from .views import (
    CommentLikeViewSet,
    CommentReportViewSet,
    CommentViewSet,
    LikeViewSet,
    UploadViewSet,
    VideoViewSet,
    ViewViewSet,
)

app_name = "videos"

router = DefaultRouter()
router.register("videos", VideoViewSet, basename="videos")
router.register("uploads", UploadViewSet, basename="uploads")
router.register("views", ViewViewSet, basename="views")
router.register("likes", LikeViewSet, basename="likes")
router.register("comments", CommentViewSet, basename="comments")
router.register("comment_likes", CommentLikeViewSet, basename="comment_likes")
router.register("comment_reports", CommentReportViewSet, basename="comment_reports")

urlpatterns = router.urls
