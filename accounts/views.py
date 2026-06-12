from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import (
    LoginForm,
    ManufacturerRegisterForm,
    DistributorRegisterForm,
    CustomerRegisterForm,
)

# def register_view(request):
#     if request.user.is_authenticated:
#         return redirect("dashboard")
#     form = RegisterForm(request.POST or None)
#     if request.method == "POST" and form.is_valid():
#         user = form.save()
#         login(request, user)
#         messages.success(request, f"Welcome, {user.first_name or user.username}!")
#         return redirect("dashboard")
#     return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("home")



from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import ManufacturerRegisterForm, DistributorRegisterForm, CustomerRegisterForm


def landing(request):
    return render(request, 'accounts/landing.html')


def home(request):
    if request.user.is_authenticated:
        return redirect('role_home')  # sends them to their dashboard
    return render(request, 'home.html')

def register_manufacturer(request):
    form = ManufacturerRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('manufacturer_home')
    return render(request, 'accounts/register_manufacturer.html', {'form': form})

def register_distributor(request):
    form = DistributorRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('distributor_home')
    return render(request, 'accounts/register_distributor.html', {'form': form})

def register_customer(request):
    form = CustomerRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('customer_home')
    return render(request, 'accounts/register_customer.html', {'form': form})

@login_required
def role_home(request):
    """Redirect logged-in users to their role-specific dashboard."""

    role = getattr(request.user, 'role', None)

    if role == 'MANUFACTURER':
        return redirect('products:dashboard')

    elif role == 'DISTRIBUTOR':
        return redirect('distributor_home')

    elif role == 'CUSTOMER':
        return redirect('customer_home')

    else:
        return redirect('products:dashboard')

        
@login_required
def manufacturer_home(request):
    from products.models import ProductModel, ProductUnit
    from blockchain.models import ScanLog

    models_list = ProductModel.objects.filter(
        manufacturer=request.user
    )

    units = ProductUnit.objects.filter(
        model__manufacturer=request.user
    ).order_by('-created_at')[:20]

    serials = ProductUnit.objects.filter(
        model__manufacturer=request.user
    ).values_list(
        'serial_number',
        flat=True
    )

    recent_scans = ScanLog.objects.filter(
        product_unit_serial__in=serials
    ).order_by('-scanned_at')[:20]

    return render(
        request,
        'accounts/manufacturer_home.html',
        {
            'models': models_list,
            'units': units,
            'recent_scans': recent_scans,
        }
    )

@login_required
def distributor_home(request):

    from products.models import ProductUnit

    units = ProductUnit.objects.filter(
        current_owner=request.user
    ).order_by('-updated_at')

    return render(
        request,
        'accounts/distributor_home.html',
        {'units': units}
    )

@login_required
def customer_home(request):
    from blockchain.models import ScanLog
    scans = ScanLog.objects.filter(user=request.user).order_by('-scanned_at')[:20]
    return render(request, 'accounts/customer_home.html', {'scans': scans})