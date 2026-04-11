from django.urls import path, include
from rest_framework.routers import DefaultRouter

from sea_saw_preference import views

router = DefaultRouter()
router.register("filter-presets", views.FilterPresetViewSet, basename="filter-preset")

app_name = "sea_saw_preference"
urlpatterns = [
    path(
        'user-column-preference/<str:table_name>/',
        views.UserColumnPreferenceViewset.as_view(),
        name='user-column-preference-list',
    ),
    path("", include(router.urls)),
]
