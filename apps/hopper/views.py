import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Hopper
from .services import (
    create_hopper_for_user,
    execute_hopper_action,
    start_race,
    compute_action_availability,
    is_game_over,
)
from .domain.exceptions import TerraHopperError


@login_required
def dashboard(request):
    hoppers = Hopper.objects.filter(user=request.user)
    leaders = Hopper.objects.select_related('user').order_by('-best_distance', '-distance')[:10]
    return render(request, 'hopper/dashboard.html', {
        'hoppers': hoppers,
        'leaders': leaders,
    })


@login_required
def create_modal(request):    return render(request, 'hopper/_create_modal.html')


@login_required
def create_hopper(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        mass_kg = request.POST.get('mass_kg', '')
        try:
            hopper = create_hopper_for_user(request.user, name, mass_kg)
            # Return updated garage fragment
            hoppers = Hopper.objects.filter(user=request.user)
            response = render(request, 'hopper/_garage_list.html', {'hoppers': hoppers})
            response['HX-Trigger'] = 'hopperCreated'
            return response
        except ValueError as e:
            return render(request, 'hopper/_create_modal.html', {'error': str(e), 'name': name, 'mass_kg': mass_kg}, status=400)
    return HttpResponse(status=405)


def get_state_payload(hopper: Hopper) -> dict:
    return {
        "id": hopper.id,
        "name": hopper.name,
        "distance": hopper.distance,
        "best_distance": hopper.best_distance,
        "strength": hopper.strength,
        "reactor_energy": hopper.reactor_energy,
        "location_state": hopper.location_state,
    }


@login_required
def hopper_game_view(request, hopper_id: int):
    # Каждый запуск заезда начинается с чистого листа: рекорд сохраняется.
    hopper = start_race(hopper_id, request.user)
    initial = get_state_payload(hopper)
    allowed = compute_action_availability(hopper)
    return render(request, 'hopper/game.html', {
        'hopper': hopper,
        'allowed': allowed,
        'game_over': is_game_over(hopper),
        'initial_state': initial,
    })


@login_required
def hopper_state_api_view(request, hopper_id: int):
    hopper = get_object_or_404(Hopper, id=hopper_id, user=request.user)
    return JsonResponse(get_state_payload(hopper))


def _game_error_response(request, hopper_id: int, message: str):
    if request.POST.get('source') == 'game':
        response = render(
            request,
            'hopper/partials/toast.html',
            {'error_message': message},
            status=400,
        )
        response['HX-Retarget'] = '#game-toast-wrap'
        response['HX-Reswap'] = 'innerHTML'
        return response
    response = render(
        request,
        'hopper/partials/action_error.html',
        {'error_message': message},
        status=400,
    )
    response['HX-Retarget'] = f'#hopper-error-{hopper_id}'
    response['HX-Reswap'] = 'innerHTML'
    return response


@login_required
@require_POST
def hopper_action_view(request, hopper_id: int):
    action_type = request.POST.get("action_type")
    use_reactor = request.POST.get("use_reactor") == "true"

    try:
        updated_hopper = execute_hopper_action(
            hopper_id=hopper_id,
            user=request.user,
            action_type=action_type,
            use_reactor=use_reactor
        )
    except TerraHopperError as e:
        if request.headers.get("HX-Request"):
            return _game_error_response(request, hopper_id, str(e))
        return JsonResponse({"error": str(e)}, status=400)

    if request.headers.get("HX-Request"):
        template = (
            "hopper/partials/game_panel.html"
            if request.POST.get("source") == "game"
            else "hopper/partials/hopper_card.html"
        )
        context = {"hopper": updated_hopper}
        if request.POST.get("source") == "game":
            context["allowed"] = compute_action_availability(updated_hopper)
            context["game_over"] = is_game_over(updated_hopper)
        response = render(
            request,
            template,
            context
        )
        response["HX-Trigger"] = json.dumps({"updateMap": get_state_payload(updated_hopper)})
        return response

    return JsonResponse({"status": "ok"})
