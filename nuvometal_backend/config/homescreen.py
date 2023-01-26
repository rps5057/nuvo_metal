from django.http import HttpResponse

def nuvometal_homescreen(request):
    home_display_text = """<h1>Welcome</h1><br>
    Here you can chose a material property and enter a range for its value.<br>
    The site returns a list of materials that fall within that range.<br>
    <br>
    <h4>Please click on the link below to see the list of available properties:</h4>
    <a href="material_search/"><h2>Material Search Menu</h2></a>"""
    return HttpResponse(home_display_text)

