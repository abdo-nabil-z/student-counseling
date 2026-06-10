from django.shortcuts import render


def home(request):
    template_name = "home_template.html"
    return render(request, template_name)