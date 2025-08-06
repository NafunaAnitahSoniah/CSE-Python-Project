from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import *
from .forms import *
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
#To handle sign up of salesagent user and the manager user
def index(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        #creating access to our form(forms.py)
        form_data = UserCreation(request.POST)
        #to check if the data posted from the UserCreation form is valid 
        if form_data.is_valid():
            #the validated data is then saved in the database table called Farmer_users
            form_data.save() 
            #directs django to pay attention to the fields username and email; and clean them
            username = form_data.cleaned_data.get('username')
            email = form_data.cleaned_data.get('email')
            #so after successfully registering, you are directed to the login form/ page
            return redirect('/login')
    #in case there is no data coming from the UserCreation form, direct to the signup.html page   
    else:
        form_data = UserCreation()
    return render(request, 'signup.html', {'form_data': form_data})

def Login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'sales_agent':

            form = login(request, user)
            return redirect('/salesagentdashboard')
        
        if user is not None and user.role == 'manager':

            form = login(request, user)
            return redirect('/managersdashboard')
        else:
            print('something is wrong')

    form = AuthenticationForm()
    
    return render(request, 'login.html', {'form':form, 'title':'login'})



def Managersdashboard(request):
    
    return render(request, 'managersdashboard.html' )

def Logout(request):
    logout(request)

    return redirect('/')
   








