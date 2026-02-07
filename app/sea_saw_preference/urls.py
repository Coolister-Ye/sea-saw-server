from django.urls import path

from sea_saw_preference import views

app_name = "sea_saw_preference"
urlpatterns = [
    path(
        'user-column-preference/<str:table_name>/',
        views.UserColumnPreferenceViewset.as_view(),
        name='user-column-preference-list',
    )
]
