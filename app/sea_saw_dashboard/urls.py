from django.urls import path
from .views import OverviewStatsView, ShippingCalendarView

urlpatterns = [
    path("overview/", OverviewStatsView.as_view(), name="dashboard-overview"),
    path("etd-calendar/", ShippingCalendarView.as_view(), name="dashboard-etd-calendar"),
]
