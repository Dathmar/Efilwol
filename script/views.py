import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.apps import apps

from users.managers import UserScriptManager

logger = logging.getLogger('console_only')


@login_required
def index(request):
    UserScript = apps.get_model('users', 'UserScript')

    # Silently repair party on every visit
    repaired = UserScript.objects.repair_party(request.user)
    if repaired:
        logger.info(f"Repaired {repaired} party slot(s) for {request.user.email}")

    party_slots = UserScript.objects.get_party_state(request.user.id)
    bench = (
        UserScript.objects
        .filter(user=request.user, party_slot__isnull=True)
        .select_related('script')
        .prefetch_related('actions')
        .order_by('script__damage_range', 'script__name')
    )

    return render(request, 'script/index.html', {
        'party_slots': party_slots,
        'bench': bench,
    })


@login_required
@require_POST
def swap_party_slot(request):
    try:
        data = json.loads(request.body)
        slot = int(data['slot'])
        user_script_id = int(data['user_script_id'])
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return JsonResponse({'ok': False, 'error': f'Invalid request: {e}'}, status=400)

    UserScript = apps.get_model('users', 'UserScript')
    try:
        party = UserScript.objects.swap_slot(slot, user_script_id, request.user.id)
        return JsonResponse({'ok': True, 'party': party})
    except PermissionError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=403)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# Legacy redirect — kept so any old bookmarks still work
def add_script_to_party(request, script_id):
    if request.user.is_authenticated:
        UserScript = apps.get_model('users', 'UserScript')
        try:
            UserScript.objects.add_to_party(script_id, request.user.id)
        except ValueError as e:
            messages.warning(request, str(e))
    return redirect(reverse('script:index'))


def remove_script_from_party(request, script_id):
    if request.user.is_authenticated:
        UserScript = apps.get_model('users', 'UserScript')
        UserScript.objects.remove_from_party(script_id, request.user.id)
    return redirect(reverse('script:index'))
