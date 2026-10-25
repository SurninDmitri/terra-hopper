from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Hopper
from .services import create_hopper_for_user


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
