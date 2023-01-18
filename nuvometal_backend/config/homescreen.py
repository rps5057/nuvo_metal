from django.http import HttpResponse

def nuvometal_homescreen(request):
    home_display_text = """<h1>You are at the homepage.</h1><br>
    <a href="material_search/"><h3>Material Search Menu</h3></a>"""
    return HttpResponse(home_display_text)

