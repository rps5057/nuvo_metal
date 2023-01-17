from django.urls import path
from . import views

app_name = 'material_search'

urlpatterns = [
    path('', views.property_index, name='property_index'),
    path('<int:property_id>/criteria/', views.property_criteria, name='property_criteria'),
    path('<int:property_id>/criteria/search', views.property_criteria_pass, name='property_criteria_pass'),
    path('<int:property_id>/criteria/<str:property_min_value>/<str:property_max_value>/search/',
         views.mat_search, name='mat_search'),
]
