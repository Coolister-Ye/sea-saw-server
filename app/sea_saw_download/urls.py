from django.urls import path

from .views import UserDownloadTasksView, DownloadTaskView

app_name = "sea_saw_download"
urlpatterns = [
    path('download-tasks/', UserDownloadTasksView.as_view(), name='download-tasks'),
    path('crm-downloads/', DownloadTaskView.as_view(), name='crm-downloads'),
]
