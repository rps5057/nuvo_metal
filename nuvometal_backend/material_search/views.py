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

data_file = 'Thermal_properties.xlsx'

mat_data_dict = data_loader(data_file)
property_value_columns = mat_data_dict['0']
mat_data = mat_data_dict['1']

# Function to write an HTML file to be used to display final result
def result_template_writer(filepath, result_data, property_name):
    html_start = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{{ 'Material Search' }}</title>
    </head>
    <body>
    <fieldset>
        <Legend><h3>{{ 'Your search criteria' }}</h3></Legend>
        <ul>
            <li>{{ 'Property: ' }}{{ property_name }}</li>
            <li>{{ 'Minimum desired value:  ' }}{{ property_min_value }}</li>
            <li>{{ 'Maximum desired value:  ' }}{{ property_max_value }}</li>
        </ul>
    </fieldset>
    <br>
    <fieldset>
        <legend><h3>{{ 'Following materials suit your criteria '}}<br></h3></legend>
        <br>
        <table border="1" class="dataframe">
        <thead> <tr style="text-align: centre;"> <th></th> <th>Material</th> <th>{{ property_name }}</th> </tr> </thead>
        <tbody>
    """
    html_end = """
        </tbody>
        </table>
    </fieldset>
    <br>
    <a href="{% url 'material_search:property_index' %}"><h3>{{ 'Do you want another search?' }}</h3></a>
    </body>
    </html>   
    """
    with open(filepath, 'w')as r_t:
        r_t.write(html_start)

    for idx in range(len(result_data)):
        template_line_value = '<tr><th>'+str(idx+1)+'</th><td>'+str(result_data['Material'][idx])+'</td><td>'+str(result_data[property_name][idx])+'</td></tr>'
        template_line = f"""
            {template_line_value}"""

        with open(filepath,'a') as r_t:
            r_t.write(template_line)

    with open(filepath,'a')as r_t:
        r_t.write(html_end)

# View to be display property menu with hyperlinks
def property_index(request):
    context = {'property_list':property_value_columns}
    return render(request, 'material_search/index.html', context)

# View to display the user input prompt for selected property
def property_criteria(request, property_id):
    min_available_value = mat_data[property_value_columns[property_id-1]].min()
    max_available_value = mat_data[property_value_columns[property_id-1]].max()
    context = {
        'min_available': min_available_value,
        'max_available': max_available_value,
        'property_id': property_id,
        'property_name': property_value_columns[property_id-1]
        }

    return render(request,'material_search/property_criteria.html', context)

# View to take the user input range of property and pass it to next view for search and display
def property_criteria_pass(request, property_id):
    property_min_value = request.POST['min_val']
    property_max_value = request.POST['max_val']

    return HttpResponseRedirect(reverse('material_search:mat_search', args=(property_id,property_min_value,property_max_value,)))

# View to search the materials within user input property range, write the template to and display the results
def mat_search(request, property_id, property_min_value, property_max_value):
    property_value_columns_idx = property_id - 1
    property_searched = property_value_columns[property_value_columns_idx]

    mat_search_criteria_1 = mat_data[property_searched] >= float(property_min_value)
    mat_search_criteria_2 = mat_data[property_searched] <= float(property_max_value)

    mat_search_result = mat_data[mat_search_criteria_1 & mat_search_criteria_2].sort_values(by=property_searched)
    response_data_df = mat_search_result.loc[:, ['Material', property_searched]]

    response_data = response_data_df.reset_index()

    result_template_file = 'material_search/templates/material_search/mat_result.html'
    result_template_writer(result_template_file, response_data, property_searched)

    context = {
        'property_name':property_searched,
        'property_min_value':property_min_value,
        'property_max_value':property_max_value,
        'response_data': response_data
    }

    return render(request, 'material_search/mat_result.html', context)
