from django.shortcuts import render,redirect
from django.http import HttpResponse
from .models import *
from django.forms import inlineformset_factory
from .forms import OrderForm,CreateUserForm
from .filters import OrderFilter
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .decorators import *
from django.contrib.auth.models import Group
from django.contrib.gis.geoip2 import GeoIP2


@login_required(login_url='login')
@admin_only
def home(request):
    customers = Customer.objects.all()
    orders = Order.objects.all()

    totalOrders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()

    print(request.user_agent.browser.family)
    print(request.user_agent.os.family + " " + request.user_agent.os.version_string)
    ip = request.META.get('REMOTE_ADDR' , None)
    print(ip)
    test_ip =  '106.209.178.138'

    g = GeoIP2()
    if ip:
        city = g.city(test_ip)['city']
    else:
        city = 'Rome' # default city

    print(city)

    context = {'customers':customers , 'orders':orders , 'total_orders':totalOrders , 'delivered':delivered , 'pending':pending}
    return render(request, 'accounts/dashboard.html' , context)

def registerPage(request):

    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()

        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                username = form.cleaned_data.get('username')

                group = Group.objects.get(name = 'customer')
                user.groups.add(group)

                Customer.objects.create(
                    user = user,
                    name = user.username,
                    email = user.email,
                )

                messages.success(request, 'Account was created for '+username)
                return redirect('login')

        context = {'form':form}
        return render(request , 'accounts/registerPage.html' , context)

@unauthenticated_user
def loginPage(request):
    context = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username = username , password = password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Username OR Password is incorrect')
            return render(request, 'accounts/loginPage.html' , context)
        
    return render(request , 'accounts/loginPage.html' , context)
    
def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def userPage(request):
    orders = request.user.customer.order_set.all()

    totalOrders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()

    context = {'orders':orders , 'total_orders':totalOrders , 'delivered':delivered , 'pending':pending }
    return render(request, 'accounts/user.html' , context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def products(request):
    products = Product.objects.all()
    return render(request, 'accounts/products.html' , {'products':products})

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def customer(request,pk):
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    order_count = orders.count()

    myFilter = OrderFilter(request.GET , queryset=orders)
    orders = myFilter.qs
    context = {'customer':customer , 'orders':orders , 'total_orders':order_count , 'myFilter':myFilter}
    return render(request, 'accounts/customer.html',context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def createOrder(request,pk):

    OrderFormSet = inlineformset_factory(Customer,Order , fields=('product' , 'status'), extra=6)

    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    # form  = OrderForm(initial={'customer':customer})

    if request.method == 'POST':
        # form = OrderForm(request.POST)
        formset = OrderFormSet(request.POST , instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('/')

    context = {"formset":formset , 'customer':customer}
    return render(request , 'accounts/order_form.html' , context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def updateOrder(request,pk):

    order = Order.objects.get(id=pk)
    form  = OrderForm(instance=order)

    if request.method == 'POST':
        form = OrderForm(request.POST , instance=order)
        if form.is_valid():
            form.save()
            return redirect('/')


    context = {'form':form}
    return render(request, 'accounts/order_form.html' , context)

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def deleteOrder(request ,pk):
    
    order  = Order.objects.get(id=pk)
    context = {'item':order}
    if request.method == "POST":
        order.delete()
        return redirect('/')
    return render(request , 'accounts/delete.html', context)
# Create your views here.

