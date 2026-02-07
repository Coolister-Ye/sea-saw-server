from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ContentTypeView, FieldListView

router = DefaultRouter()
router.register(r"fields", FieldListView)

app_name = "sea-saw-base"
urlpatterns = [
    path("", include(router.urls)),
    path("content-types/", ContentTypeView.as_view(), name="content-types"),
]
