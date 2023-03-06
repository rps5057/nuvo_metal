import pandas as pd

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import timezone
from django.db.models import Min, Max, Count
from django.urls import reverse

from .models import MaterialProperties, PropertiesList, PropertySearch
from .data_loader import data_to_db, search_the_db


# data file and lists of properties in the Excel file and  their units
data_file = 'Thermal_properties.xlsx'
property_value_keys = ['Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat']
property_units_SI = ['K', 'W/m-K', 'kg/m3', 'kJ/kg-K']
material_properties_all_fields = ['material_name', 'material_type', 'melting_point', 'thermal_conductivity', 'density',
                                  'specific_heat']
material_properties_property_fields = ['melting_point', 'thermal_conductivity', 'density', 'specific_heat']

# loading data to db
try:
    material_data_db = MaterialProperties.objects.all()
    if not material_data_db:
        flag = data_to_db(data_file, property_value_keys, property_units_SI)
        db_status = 'Database has been now populated'
    else:
        flag = 0
        db_status = 'Database already has some data.'
    print(db_status)
except Exception as err_msg:
    print(err_msg)


# build a dataframe with name, number, unit, min and max available value in the database for all properties
def summarize_data():
    """
    :return: dataframe, summary of data available in the database
    """
    properties_summary_columns = ['property_no', 'property_name', 'property_unit', 'min_available_db',
                                  'max_available_db', 'total_data_points']
    properties_summary_df = pd.DataFrame(columns=properties_summary_columns)

    for idx in range(len(property_value_keys)):
        # getting data from the PropertiesList model
        current_property_no = idx+1
        current_property = PropertiesList.objects.get(property_no=current_property_no)
        properties_summary_df.loc[idx, 'property_no'] = current_property.property_no
        properties_summary_df.loc[idx, 'property_name'] = current_property.property_name
        properties_summary_df.loc[idx, 'property_unit'] = current_property.property_unit_si

        # getting data from MaterialsProperties model
        current_field = material_properties_property_fields[idx]

        for v in MaterialProperties.objects.aggregate(Min(current_field)).values():
            properties_summary_df.loc[idx, 'min_available_db'] = v

        for v in MaterialProperties.objects.aggregate(Max(current_field)).values():
            properties_summary_df.loc[idx, 'max_available_db'] = v

        for v in MaterialProperties.objects.aggregate(Count(current_field)).values():
            properties_summary_df.loc[idx, 'total_data_points'] = v

    return properties_summary_df


try:
    properties_summary = summarize_data()
    print(properties_summary)
except Exception as err_msg:
    print(err_msg)


# validation function to check if the user input is blank
def check_input_for_blank(request):
    """
    PropertySearch: method, (property_no, property_name, minimum_value, maximum_value, search_date)
    :param request
    :return: str, error message in case of no input from user
    """
    if request.POST['min_val'] == "" or request.POST['max_val'] == "":
        input_blank_msg = "Please enter both the minimum and maximum desired values for your chosen property."
    else:
        input_blank_msg = ""

    return input_blank_msg
    
    
# validation function to check if the user input values are in the range available in database
def check_input_property_range(user_search_obj):
    """
    properties_summary: df, ('property_no', 'property_name', 'property_unit', 'min_available_db', 'max_available_db',
            'total_data_points')
    PropertySearch: method, (property_no, property_name, minimum_value, maximum_value, search_date)
    :param user_search_obj:
    :return: str, message to be passed to template for display
    """
    min_available_value = properties_summary.loc[user_search_obj.property_no - 1, 'min_available_db']
    max_available_value = properties_summary.loc[user_search_obj.property_no - 1, 'max_available_db']

    if user_search_obj.minimum_value > user_search_obj.maximum_value:
        input_error_msg = 'Please check the input values, make sure minimum input is not more than maximum input.'
    elif user_search_obj.minimum_value > max_available_value:
        # input range fully above avaialable data
        input_error_msg = """
            Minimum value more than highest available value in database.
            Please try again within available range.
            """
    elif user_search_obj.maximum_value < min_available_value:
        # input range fully below available range
        input_error_msg = """
            Maximum value less than least available value in database.
            Please try again within available range.
            """
    else:
        input_error_msg = ''

    return input_error_msg


# function to check the relation between user input property range and available dataset range
# Generates display message to be displayed with search results
def input_property_range_vs_db_range(user_search_obj):
    """
    properties_summary: df, ('property_no', 'property_name', 'property_unit', 'min_available_db', 'max_available_db',
            'total_data_points')
    PropertySearch: method, (property_no, property_name, minimum_value, maximum_value, search_date)
    :param user_search_obj:
    :return: str, message to be displayed with search result
    """
    min_available_value = properties_summary.loc[user_search_obj.property_no-1, 'min_available_db']
    max_available_value = properties_summary.loc[user_search_obj.property_no-1, 'max_available_db']

    if user_search_obj.minimum_value < min_available_value:
        if user_search_obj.maximum_value > max_available_value:
            # available range is subset of input range
            result_msg = 'Input range larger than available range.'
        else:
            # minimum input below and maximum input in avalable range
            result_msg = 'Input range starts below the available range.'
    else:
        if user_search_obj.maximum_value > max_available_value:
            # minimum input in and maximum input above avalable range
            result_msg = 'Input range ends above available range.'
        else:
            # input range is subset of available range
            result_msg = 'Optimum input range.'
    return result_msg


# Create your views here.
def home_screen(request):
    return render(request, 'material_search/home_screen.html')


def property_menu(request):
    context = {'property_list': property_value_keys,
               'data_summary': properties_summary.to_records(index=False)
               }

    return render(request, 'material_search/property_menu.html', context)


def search_criteria(request, property_no):
    properties_summary_idx = property_no - 1

    try:
        property_requested = PropertiesList.objects.get(property_no=property_no)
    except PropertiesList.DoesNotExist:
        raise Http404("Property does not exist")

    context = {
                'property_requested': property_requested,
                'min_available': properties_summary.loc[properties_summary_idx, 'min_available_db'],
                'max_available': properties_summary.loc[properties_summary_idx, 'max_available_db'],
                'criteria_error_msg': '',
            }
    return render(request, 'material_search/search_criteria_form.html', context)


def user_input_to_db(request, property_no):
    blank_error_msg = check_input_for_blank(request)
    if blank_error_msg:
        context = {
            'property_requested': PropertiesList.objects.get(property_no=property_no),
            'min_available': properties_summary.loc[property_no - 1, 'min_available_db'],
            'max_available': properties_summary.loc[property_no - 1, 'max_available_db'],
            'criteria_error_msg': blank_error_msg,
        }
        return render(request, 'material_search/search_criteria_form.html', context)
    else:
        current_search = PropertySearch(
                            property_no=property_no,
                            property_name=PropertiesList.objects.get(property_no=property_no),
                            minimum_value=float(request.POST['min_val']),
                            maximum_value=float(request.POST['max_val']),
                            search_date=timezone.now(),
                        )

    input_error_msg = check_input_property_range(current_search)
    if not input_error_msg:
        current_search.save()
        search_id = current_search.id
        return HttpResponseRedirect(reverse('material_search:search_result', args=(property_no, search_id,)))
    else:
        context = {
            'property_requested': current_search.property_name,
            'min_available': properties_summary.loc[current_search.property_no - 1, 'min_available_db'],
            'max_available': properties_summary.loc[current_search.property_no - 1, 'max_available_db'],
            'criteria_error_msg': input_error_msg,
        }
        return render(request, 'material_search/search_criteria_form.html', context)


def search_result(request, property_no, search_id):
    search_obj = PropertySearch.objects.get(id=search_id)
    result_queryset = search_the_db(search_id, search_obj.minimum_value, search_obj.maximum_value)
    result_df = pd.DataFrame(columns=['Material', search_obj.property_name.property_name])

    result_msg = input_property_range_vs_db_range(search_obj)

    for idx in range(result_queryset.count()):
        queryset_obj = result_queryset[idx]
        result_df.loc[idx, 'Material'] = queryset_obj.material_name
        result_df.loc[idx, search_obj.property_name.property_name] = getattr(
            queryset_obj, material_properties_property_fields[search_obj.property_no-1]
            )
    context = {
        'search_obj': search_obj,
        'result_array': result_df.to_records(index=False),
        'count': len(result_df),
        'display_msg': result_msg,
        }
    return render(request, 'material_search/search_result.html', context)

