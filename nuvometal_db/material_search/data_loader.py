import pandas as pd
from .models import PropertiesList, MaterialProperties, PropertySearch

# data file and lists of properties in the excel file and  their units
data_file = 'Thermal_properties.xlsx'
property_value_keys = ['Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat']
property_units_SI = ['K', 'W/m-K', 'kg/m3', 'kJ/kg-K']


# function to load data from excel file into dataframe and clean it
def data_loader(filename, property_value_keys):
    # load data from excel file into dataframe with specified column names
    column_names = ['Material', 'Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat', 'Composite Index']
    mat_data = pd.read_excel(filename, names=column_names, skiprows=[0])
    mat_data.drop(['Composite Index'], axis=1, inplace=True)

    # add a column named 'Material Type' to the dataframe
    mat_type = ['Metals', 'Plastics', 'Woods', 'Hardwood', 'Softwood', 'Misc Wood', 'Miscellaneous']
    mat_type_idxs = [0, 22, 53, 54, 66, 83, 89, len(mat_data)]

    def add_mat_type(df, initial_idx, next_idx, mat_type):
        final_idx = next_idx - 1
        df.loc[initial_idx:final_idx, 'Material Type'] = mat_type

    for idx in range(len(mat_type_idxs) - 1):
        initial_idx = mat_type_idxs[idx]
        next_idx = mat_type_idxs[idx + 1]
        add_mat_type(mat_data, initial_idx, next_idx, mat_type[idx])

    # drop those rows that have no value in all of the property columns
    mat_data.drop(mat_data[mat_data.loc[:,
                           ['Melting Point', 'Thermal Conductivity', 'Density', 'Specific Heat']].isnull().all(
        1)].index, axis=0, inplace=True)
    mat_data.reset_index(drop=True, inplace=True)

    # finding and dropping those columns that have string value in property columns
    bad_data_indices_dict = {}

    for element in property_value_keys:
        bad_data_indices_dict[element] = list(mat_data[mat_data[element].map(type) == str].index)

    for element in bad_data_indices_dict:
        if bad_data_indices_dict[element]:
            mat_data.drop(bad_data_indices_dict[element], axis=0, inplace=True)
            continue

    mat_data.reset_index(drop=True, inplace=True)

    # return the dataframe with cleaned data
    return mat_data

# function to load the clean data from dataframe to database
def data_to_db(data_file, property_value_keys, property_units_SI):
    # Loading the cleaned data into pandas dataframe 'mat_data'
    mat_data = data_loader(data_file, property_value_keys)
    flag = 0
    # load values to PropertiesList
    for element in range(len(property_value_keys)):
        pl = PropertiesList(
                property_no=element + 1,
                property_name=property_value_keys[element],
                property_unit_si=property_units_SI[element]
            )
        pl.save()
    flag = flag + 1
# load the values to MaterialProperties
    for element in range(len(mat_data)):
        mp = MaterialProperties(
                material_name=mat_data.loc[element,'Material'],
                material_type=mat_data.loc[element,'Material Type'],
                melting_point=mat_data.loc[element,property_value_keys[0]],
                thermal_conductivity=mat_data.loc[element,property_value_keys[1]],
                density=mat_data.loc[element,property_value_keys[2]],
                specific_heat=mat_data.loc[element,property_value_keys[3]],
            )
        mp.save()

    flag = flag +2
    return flag

def search_the_db(search_id, min_value, max_value):
    search_obj = PropertySearch.objects.get(id=search_id)
    property_no = search_obj.property_no

    if property_no == 1:
        result_obj = MaterialProperties.objects.get(melting_point__gte=min_value, melting_poit__lte=max_value).order_by('-melting_point')
    elif property_no == 2:
        result_obj = MaterialProperties.objects.filter(thermal_conductivity__gte=min_value, thermal_conductivity__lte=max_value).order_by('-thermal_conductivity')
    elif property_no == 3:
        result_obj = MaterialProperties.objects.get(density__gte=min_value, density__lte=max_value).order_by('-density')
    elif property_no == 4:
        result_obj = MaterialProperties.objects.get(specific_heat__gte=min_value, specific_heat__lte=max_value).order_by('-specific_heat')
    else:
        result_obj = ''

    if result_obj:
        print(result_obj)
        print(type(result_obj))
    else:
        print('No data found')

    return result_obj
