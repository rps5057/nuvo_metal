from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

import pandas as pd

# Create your views here.

# Function to load the data from excel file to a pandas dataframe, add 'Material Type' column,
# and drop all rows with no property data in them
def data_loader(filename):
    column_names = ['Material', 'Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat', 'Composite Index']
    mat_data = pd.read_excel(filename, names=column_names, skiprows=[0])
    mat_data.drop(['Composite Index'], axis=1, inplace=True)

    mat_type = ['Metals', 'Plastics', 'Woods','Hardwood', 'Softwood', 'Misc Wood', 'Miscellaneous']
    mat_type_idxs = [0, 22, 53, 54, 66, 83, 89, len(mat_data)]

    def add_mat_type(df, initial_idx, next_idx, mat_type):
        final_idx = next_idx-1
        df.loc[initial_idx:final_idx, 'Material Type'] = mat_type

    for idx in range(len(mat_type_idxs)-1):
        initial_idx = mat_type_idxs[idx]
        next_idx = mat_type_idxs[idx+1]
        add_mat_type(mat_data,initial_idx, next_idx, mat_type[idx])

    mat_data.drop(mat_data[mat_data.loc[:,['Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat']].isnull().all(1)].index, axis=0, inplace=True)
    mat_data.reset_index(drop=True, inplace=True)

    property_value_keys = ['Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat']
    bad_data_indices_dict = {}

    for element in property_value_keys:
        bad_data_indices_dict[element] = list(mat_data[mat_data[element].map(type) == str].index)

    for element in bad_data_indices_dict:
        if bad_data_indices_dict[element]:
            mat_data.drop(bad_data_indices_dict[element], axis=0, inplace=True)
            continue

    mat_data.reset_index(drop=True, inplace=True)

    return_data_dict = {'0':property_value_keys, '1':mat_data}

    return return_data_dict

# Loading data into pandas dataframe 'mat_data'
data_file = 'Thermal_properties.xlsx'

mat_data_dict = data_loader(data_file)
property_value_columns = mat_data_dict['0']
mat_data = mat_data_dict['1']

# Creatig dataframe with property, SI unit, minimum and maximum available value in the datafile 
property_units_SI = {'Melting Point':'K', 'Thermal Conductivity':'W/m-K', 'Density':'kg/m3', 'Specific Heat':'kJ/kg-K'}

properties_summary_column_names = ['property_name', 'property_unit_SI', 'min_value_in_db', 'max_value_in_db']
properties_summary = pd.DataFrame(columns=properties_summary_column_names)

for idx in range(len(property_value_columns)):
    current_property_name = property_value_columns[idx]
    min_available_value_temp = mat_data[current_property_name].min()
    max_available_value_temp = mat_data[current_property_name].max()
    property_unit_name = property_units_SI[current_property_name]
    
    current_property_summary = [current_property_name, property_unit_name, min_available_value_temp, max_available_value_temp]
    properties_summary.loc[idx,properties_summary_column_names]=current_property_summary
    
# Functions for User input cross check agaianst available data
def input_range_validation_1(property_id, input_min_value, input_max_value):
    min_available_value = properties_summary.loc[property_id-1,'min_value_in_db']
    max_available_value = properties_summary.loc[property_id-1,'max_value_in_db'] 
    
    if input_min_value > input_max_value:
        return_message = 'Please check the input values, make sure minimum input is not more than maximum input.'
        #break
    elif input_min_value > max_available_value:
        # input range fully above avaialable data
        return_message = 'Minimum value more than highest available value in databse.Please try again within available range.'   
    elif input_max_value < min_available_value:
        # input range fully below available range
        return_message = 'Maximum value less than least available value in databse.Please try again within available range.'
    else:
        return_message = ''
        
    return return_message        

def input_range_validation_2(property_id, input_min_value, input_max_value):
    min_available_value = properties_summary.loc[property_id-1,'min_value_in_db']
    max_available_value = properties_summary.loc[property_id-1,'max_value_in_db']
    
    if input_min_value < min_available_value:
        if input_max_value > max_available_value:
            # available range is subset of input range
            return_message = 'Input range larger than available range.'
        else:
            # minimum input below and maximum input in avalable range
            return_message = 'Input range starts below the available range.'
    else: 
        if input_max_value > max_available_value:
            # minimum input in and maximum input above avalable range
            return_message = 'Input range ends above available range.'
        else:
            # input range is subset of available range
            return_message = 'Optimum input range.'            
    return return_message

# View to be display property menu with hyperlinks
def property_index(request):
    context = {'property_list':property_value_columns}    
    return render(request, 'material_search/index.html', context)

# View to display the user input prompt for selected property
def property_criteria(request, property_id):
    min_available_value = properties_summary.loc[property_id-1,'min_value_in_db']
    max_available_value = properties_summary.loc[property_id-1,'max_value_in_db']
    chosen_property_unit = properties_summary.loc[property_id-1,'property_unit_SI']
    
    context = {
        'min_available': min_available_value,
        'max_available': max_available_value,
        'property_id': property_id,
        'property_name': property_value_columns[property_id-1],
        'property_unit' : chosen_property_unit,
        #'template_error_message' : error_message
        }

    return render(request,'material_search/property_criteria.html', context)

# View to take the user input range of property and pass it to next view for search and display
def property_criteria_pass(request, property_id):
    property_min_value = request.POST['min_val']
    property_max_value = request.POST['max_val']
       
    return HttpResponseRedirect(reverse('material_search:mat_search', args=(property_id,property_min_value,property_max_value)))


# View to search the materials within user input property range, write the template to and display the results
def mat_search(request, property_id, property_min_value, property_max_value):
    property_value_columns_idx = property_id - 1
    property_searched = property_value_columns[property_value_columns_idx]
    property_unit = properties_summary.loc[property_id-1,'property_unit_SI']
    
    error_message = input_range_validation_1(property_id, float(property_min_value), float(property_max_value))
    if error_message:
        min_available_value = properties_summary.loc[property_id-1,'min_value_in_db']
        max_available_value = properties_summary.loc[property_id-1,'max_value_in_db']
        chosen_property_unit = properties_summary.loc[property_id-1,'property_unit_SI']
        context = {
        'min_available': min_available_value,
        'max_available': max_available_value,
        'property_id': property_id,
        'property_name': property_value_columns[property_id-1],
        'property_unit' : chosen_property_unit,
        'template_error_message' : error_message,
        }

        return render(request,'material_search/property_criteria.html', context)
    
    display_message = input_range_validation_2(property_id, float(property_min_value), float(property_max_value))

    mat_search_criteria_1 = mat_data[property_searched] >= float(property_min_value)
    mat_search_criteria_2 = mat_data[property_searched] <= float(property_max_value)

    mat_search_result = mat_data[mat_search_criteria_1 & mat_search_criteria_2].sort_values(by=property_searched)
    response_data_df = mat_search_result.loc[:, ['Material', property_searched]]
    
    if len(response_data_df) == 0:
        result_message = 'Sorry, No materials found in the database!'
    else:
        result_message = ''
        
    response_data_df.reset_index(inplace=True)
    response_data = response_data_df.to_html()

    index_url = reverse('material_search:property_index')
    html_start_direct = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Material Search</title>
        </head>
        <body>
        <fieldset>
            <Legend><h3>Your search criteria</h3></Legend>
            <ul>
                <li>Property:{property_searched}</li>
                <li>Minimum desired value: {property_min_value} {property_unit}</li>
                <li>Maximum desired value: {property_max_value} {property_unit}</li>
            </ul>
            {display_message}
        </fieldset>
        <br>
        <fieldset>
            <legend><h3>List of Materials and {property_searched} (in {property_unit}) matching your criteria<br></h3></legend>
            <br>
    """
    html_end_direct = f"""
       <br>
       {result_message}
       <a href="{index_url}"><h3>Do you want another search?</h3></a>
       </fieldset>
       </body>
       </html>   
       """

    response_string = html_start_direct+response_data+html_end_direct
    return HttpResponse(response_string)