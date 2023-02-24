from django.db import models


# Create your models here.
class PropertiesList(models.Model):
    property_no = models.IntegerField('Property Number', unique=True)
    property_name = models.CharField('Property Name', max_length=200)
    property_unit_si = models.CharField('SI unit', max_length=100)

    def __str__(self):
        return self.property_name


class MaterialProperties(models.Model):
    material_name = models.CharField('Material Name', max_length=200)
    material_type = models.CharField('Type of Material', max_length=100)
    melting_point = models.FloatField('Melting Point', null=True)
    thermal_conductivity = models.FloatField('Thermal Conductivity', null=True)
    density = models.FloatField('Density', null=True)
    specific_heat = models.FloatField('Specific Heat', null=True)

    def __str__(self):
        return self.material_name


class PropertySearch(models.Model):
    property_no = models.IntegerField('Property Number', unique=False)
    property_name = models.ForeignKey(PropertiesList, models.SET_NULL, null=True)
    minimum_value = models.FloatField('Minimum User Input Value')
    maximum_value = models.FloatField('Maximum User Input Value')
    search_date = models.DateTimeField('Time of Query')

    def __str__(self):
        return str(self.search_date)
