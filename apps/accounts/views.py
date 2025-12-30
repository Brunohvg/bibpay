from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages


def login_view(request):
    """
    View para login de usuário.
    
    GET: Renderiza formulário de login
    POST: Processa login e redireciona para dashboard
    """
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard-home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo, {username}!')
                
                # Redirecionar para 'next' se existir, senão para dashboard
                next_url = request.GET.get('next', 'dashboard:index')
                return redirect(next_url)
        else:
            messages.error(request, 'Usuário ou senha inválidos')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    View para logout de usuário.
    
    POST: Faz logout e redireciona para login
    """
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('accounts:login')


def signup_view(request):
    """
    View para cadastro de novo usuário.
    
    GET: Renderiza formulário de cadastro
    POST: Cria novo usuário e faz login automático
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo!')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Erro ao criar conta. Verifique os dados.')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})
