from django.shortcuts import render, reverse, redirect
from django.apps import apps

from django.urls import reverse


# Create your views here.
def index(request):
    user_scripts = None
    if request.user.is_authenticated:
        user_scripts = apps.get_model('users', 'UserScript').objects.filter(user=request.user)

    return render(request, 'script/index.html', {'user_scripts': user_scripts})

def add_script_to_party(request, script_id):
    if request.user.is_authenticated:
        user_script_model = apps.get_model('users', 'UserScript')
        user_script_model.objects.add_to_party(script_id, request.user.id)

    return redirect(reverse('script:index'))

def remove_script_from_party(request, script_id):
    if request.user.is_authenticated:
        user_script_model = apps.get_model('users', 'UserScript')
        user_script_model.objects.remove_from_party(script_id, request.user.id)

    return redirect(reverse('script:index'))