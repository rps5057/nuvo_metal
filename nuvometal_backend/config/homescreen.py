from django.http import HttpResponse

def nuvometal_homescreen(request):
    return HttpResponse('<h1>You are at the homepage.</h1><br>Add "material_search/" to go to search menu.')
    #return HttpResponse('This is the home screen for property based material search <br> property list: <br> '
    #                    '1. Melting point, <br>'
    #                    '2.Thermal conductivity, <br>'
    #                    '3.Density, <br>'
    #                    '4.Specific Heat')

def nuvometal_property(request, property_id):
    if property_id > 4 or property_id < 0:
        return HttpResponse('Check property id')
    elif property_id == 1:
        property_name = 'Melting Point'
    elif property_id == 2:
        property_name = 'Thermal conductivity'
    elif property_id == 3:
        property_name = 'Density'
    elif property_id == 4:
        property_name = 'Specific heat'
    return HttpResponse(f'Please add the lower and upper limits for {property_id}. {property_name}')
