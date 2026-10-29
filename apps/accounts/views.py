from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import RegisterForm, LoginForm


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def index(request):
    if request.user.is_authenticated:
        return redirect('hopper:dashboard')
    return redirect('login')


def register(request):
    if request.user.is_authenticated:
        return redirect('hopper:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            tokens = get_tokens_for_user(user)
            response = redirect('hopper:dashboard')
            response.set_cookie('access_token', tokens['access'], httponly=True, samesite='Lax', max_age=15 * 60)
            response.set_cookie('refresh_token', tokens['refresh'], httponly=True, samesite='Lax', max_age=7 * 24 * 60 * 60)
            return response
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('hopper:dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            tokens = get_tokens_for_user(user)
            response = redirect('hopper:dashboard')
            response.set_cookie('access_token', tokens['access'], httponly=True, samesite='Lax', max_age=15 * 60)
            response.set_cookie('refresh_token', tokens['refresh'], httponly=True, samesite='Lax', max_age=7 * 24 * 60 * 60)
            return response
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    response = redirect('login')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response
