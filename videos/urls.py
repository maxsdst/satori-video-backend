from rest_framework.routers import DefaultRouter

from .views import (
    CommentLikeViewSet,
    CommentReportViewSet,
    CommentViewSet,
    LikeViewSet,
    ReportViewSet,
    SavedVideoViewSet,
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
router.register("reports", ReportViewSet, basename="reports")
router.register("comments", CommentViewSet, basename="comments")
router.register("comment_likes", CommentLikeViewSet, basename="comment_likes")
router.register("comment_reports", CommentReportViewSet, basename="comment_reports")
router.register("saved_videos", SavedVideoViewSet, basename="saved_videos")

urlpatterns = router.urls
