from django.urls import path

from preference import views

app_name = "preference"
urlpatterns = [
    path(
        'user-column-preference/<str:table_name>/',
        views.UserColumnPreferenceViewset.as_view(),
        name='user-column-preference-list',
    )
]
