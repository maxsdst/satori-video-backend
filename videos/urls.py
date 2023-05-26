from rest_framework.routers import DefaultRouter

from .views import UploadViewSet, VideoViewSet


router = DefaultRouter()
router.register("videos", VideoViewSet)
router.register("uploads", UploadViewSet)

urlpatterns = router.urls
