from django.urls import path
from . import views


app_name = 'script'
urlpatterns = [
    path('', views.index, name='index'),
    path('script/party/add/<int:script_id>/', views.add_script_to_party, name='add-to-party'),
    path('script/party/remove/<int:script_id>/', views.remove_script_from_party, name='remove-from-party'),
]
