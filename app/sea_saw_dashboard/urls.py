from django.urls import path
from .views import OverviewStatsView, ETDCalendarView

urlpatterns = [
    path("overview/", OverviewStatsView.as_view(), name="dashboard-overview"),
    path("etd-calendar/", ETDCalendarView.as_view(), name="dashboard-etd-calendar"),
]
