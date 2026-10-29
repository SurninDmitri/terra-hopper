from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Hopper
from .services import create_hopper_for_user, execute_hopper_action
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
def create_modal(request):
    return render(request, 'hopper/_create_modal.html')


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
            response = render(
                request,
                "hopper/partials/action_error.html",
                {"error_message": str(e)},
                status=400
            )
            response["HX-Retarget"] = f"#hopper-error-{hopper_id}"
            response["HX-Reswap"] = "innerHTML"
            return response
        return JsonResponse({"error": str(e)}, status=400)

    if request.headers.get("HX-Request"):
        return render(
            request,
            "hopper/partials/hopper_card.html",
            {"hopper": updated_hopper}
        )

    return JsonResponse({"status": "ok"})
