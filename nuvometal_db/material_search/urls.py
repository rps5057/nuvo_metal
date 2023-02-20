"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

app_name = 'material_search'

urlpatterns = [
    path('', views.homescreen, name='homescreen'),
    path('material search/', views.property_menu, name='menu'),
    path('material search/<int:property_no>/search criteria/', views.search_criteria, name='search_criteria'),
    path('material search/<int:property_no>/search/', views.user_input_to_db, name='user_input_to_db'),
    path('material_search/<int:property_no>/<int:search_id>/result', views.search_result, name='search_result'),

]
