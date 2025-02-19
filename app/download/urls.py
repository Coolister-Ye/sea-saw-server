from django.urls import path

from . import views

app_name = "download"
urlpatterns = [path('download-tasks/', views.UserDownloadTasksView.as_view(), name='download-tasks')]
