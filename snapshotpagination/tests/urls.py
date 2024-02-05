from rest_framework.routers import DefaultRouter

from .views import ItemViewSet


app_name = "snapshotpagination_tests"

router = DefaultRouter()
router.register("item", ItemViewSet, basename="items")

urlpatterns = router.urls
