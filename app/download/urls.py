from django.urls import path
<<<<<<< HEAD

from . import views

app_name = "download"
urlpatterns = [path('download-tasks/', views.UserDownloadTasksView.as_view(), name='download-tasks')]
=======
from . import views

app_name = "download"
urlpatterns = [
    path('download-tasks/', views.UserDownloadTasksView.as_view(), name='download-tasks'),
]
>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787
