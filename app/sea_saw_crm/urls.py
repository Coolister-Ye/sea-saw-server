from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'contacts', views.ContactViewSet)
router.register(r'companies', views.CompanyViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'contracts', views.ContractViewSet)
router.register(r'products', views.ProductViewSet)

app_name = "sea-saw-crm"
urlpatterns = [
    path('', include(router.urls)),
    path('fields/', views.FieldListView.as_view(), name='fields'),
    path('contracts-stats/', views.ContractStats.as_view(), name='contracts-stats'),
    path('orders-stats/', views.OrderStats.as_view(), name='contracts-stats'),
    path('orders-stats/s2/', views.OrderStatsByMonth.as_view(), name='contracts-stats-s2'),
    path('download/', views.DownloadTaskView.as_view(), name='download'),
]
