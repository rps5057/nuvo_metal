from django.contrib import admin

# Register your models here.
from .models import PropertiesList, MaterialProperties, PropertySearch

admin.site.register(PropertiesList)
admin.site.register(MaterialProperties)
admin.site.register(PropertySearch)