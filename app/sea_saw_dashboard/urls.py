from django.urls import path
from .views import OverviewStatsView

urlpatterns = [
    path("overview/", OverviewStatsView.as_view(), name="dashboard-overview"),
]
