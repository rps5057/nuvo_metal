import pandas as pd

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.db.models import Min, Max, Count
from django.urls import reverse

from .models import MaterialProperties, PropertiesList, PropertySearch
from .data_loader import data_to_db, search_the_db


# data file and lists of properties in the excel file and  their units
data_file = 'Thermal_properties.xlsx'
property_value_keys = ['Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat']
property_units_SI = ['K', 'W/m-K', 'kg/m3', 'kJ/kg-K']
material_properties_all_fields = ['material_name', 'material_type', 'melting_point', 'thermal_conductivity', 'density', 'specific_heat']
material_properties_property_fields = ['melting_point', 'thermal_conductivity', 'density', 'specific_heat']

# loading data to db
material_data_db = MaterialProperties.objects.all()

if material_data_db:
    flag = 0
    db_status = 'Database already has some data.'
else:
    flag = data_to_db(data_file, property_value_keys,property_units_SI)
    db_status = 'Database has been now populated'

print(db_status)

# build a dataframe with name, number, unit, min and max available value in the database for all properties
def summarize_data():
    properties_summary_columns = ['property_no','property_name', 'property_unit', 'min_available_db',
                                  'max_available_db', 'total_data_points']
    properties_summary = pd.DataFrame(columns=properties_summary_columns)

    for idx in range(len(property_value_keys)):
        # getting data from the PropertiesList model
        current_property_no = idx+1
        current_property = PropertiesList.objects.get(property_no=current_property_no)
        properties_summary.loc[idx, 'property_no'] = current_property.property_no
        properties_summary.loc[idx, 'property_name'] = current_property.property_name
        properties_summary.loc[idx, 'property_unit'] = current_property.property_unit_si

        #getting data from MaterialsProperties model
        current_field = material_properties_property_fields[idx]
        min_key = current_field + '__min'
        max_key = current_field + '__max'
        count_key = current_field + '__count'
        
        current_min_obj = MaterialProperties.objects.aggregate(Min(current_field))
        current_max_obj = MaterialProperties.objects.aggregate(Max(current_field))
        current_count_obj = MaterialProperties.objects.aggregate(Count(current_field))

        properties_summary.loc[idx, 'min_available_db'] = current_min_obj[min_key]
        properties_summary.loc[idx, 'max_available_db'] = current_max_obj[max_key]
        properties_summary.loc[idx, 'total_data_points'] = current_count_obj[count_key]
            #getattr(current_max_obj, max_attr)
    return properties_summary

properties_summary = summarize_data()
print(properties_summary)

# Create your views here.

def homescreen(request):
    return render(request, 'material_search/homescreen.html')
    
def property_menu(request):
    context = {'property_list': property_value_keys}
    return render(request, 'material_search/property_menu.html', context)
    
def search_criteria(request, property_no):
    properties_summary_idx = property_no - 1

    try:
        property_requested = PropertiesList.objects.get(property_no=property_no)
    except PropertiesList.DoesNotExist:
        raise Http404("Property does not exist")

    context = {
                'property_requested': property_requested,
                'min_available':properties_summary.loc[properties_summary_idx, 'min_available_db'],
                'max_available':properties_summary.loc[properties_summary_idx, 'max_available_db'],
                'criteria_error_msg':'',
            }
    return render(request, 'material_search/search_criteria_form.html', context)

def user_input_to_db(request,property_no):
    search_min_value = request.POST['min_val']
    search_max_value = request.POST['max_val']
    current_search = PropertySearch(
                            property_no=property_no,
                            property_name=PropertiesList.objects.get(property_no=property_no),
                            minimum_value=float(search_min_value),
                            maximum_value=float(search_max_value),
                            search_date=timezone.now(),
                        )
    current_search.save()
    search_id = current_search.id
    return HttpResponseRedirect(reverse('material_search:search_result', args=(property_no,search_id,)))


def search_result(request,property_no,search_id):
    search_obj = PropertySearch.objects.get(id=search_id)
    property_name = str(search_obj.property_name)
    min_value = search_obj.minimum_value
    max_value = search_obj.maximum_value
    result_queryset = search_the_db(search_id, min_value, max_value)
    material_count = result_queryset.count()
    result_df = pd.DataFrame(columns=['Material', 'Property'])
    for idx in range(material_count):
        queryset_obj = result_queryset[idx]
        result_df.loc[idx,'Material'] = queryset_obj.material_name
        #result_df.loc[idx,'Property'] = getattr(queryset_obj, property_name)
        result_df.loc[idx, 'Property'] = getattr(queryset_obj, 'thermal_conductivity')

    result_df_html = result_df.to_html()
    return HttpResponse(result_df_html)
    #return HttpResponse(f'{material_count} material(s) found.')