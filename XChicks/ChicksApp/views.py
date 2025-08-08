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
def indexpage(request):
    details = request.objects.all().order_by('-id')
    return render(request, 'index.html',{'details': details})

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


#For the Managers

def Managersdashboard(request):
    
    return render(request, 'managersdashboard.html' )

def ViewChickRequests(request):

    return render(request, 'viewChickrequests.html')

def ViewFeedRequests(request):

    return render(request, 'viewFeedAllocations.html')

def FarmerReview(request):
     return render(request, 'farmerReview.html')

def Approverequest(request):
    return render(request, 'approveRequest.html')


def FarmerRecords(request):
     return render(request, 'farmerRecords.html')

def chickStock(request):
    return render(request, 'chickStock.html')

def feedStock(request):
    return render(request, 'feedStock.html')

def UpdateChickStock(request):

    return render(request, 'updateChickStock.html')

def UpdateFeedStock(request):

    return render(request, 'updateFeedStock.html')

def Reports(request):

    return render(request, 'reports.html')

def Sales(request):

    return render(request, 'sales.html')



def DeleteRequest(request):
     return render(request, 'deleteRequest.html')




#For the Sales Agents
def SalesAgentdashboard(request):
    return render(request, '1salesAgentdashboard.html')

@login_required
def AddChickRequest(request):
        if request.method == 'POST':
            # Extract form data
            farmer_id = request.POST.get('farmer')
            chick_request_id = request.POST.get('chick_request_id')
            farmer_type = request.POST.get('farmer_type')
            chick_type = request.POST.get('chick_type')
            chick_breed = request.POST.get('chick_breed')
            quantity = request.POST.get('quantity')
            chick_period = request.POST.get('chick_period')
            # Convert feed_taken to boolean
            feed_taken = request.POST.get('feed_taken') == 'True'  
            payment_terms = request.POST.get('payment_terms')
            received_through = request.POST.get('received_through')

            # Get the farmer instance
            farmer = get_object_or_404(Customer, id=farmer_id)

            # Create a new ChickRequest instance
            chick_request = ChickRequest(
                farmer=farmer,
                chick_request_id=chick_request_id,
                farmer_type=farmer_type,
                chick_type=chick_type,
                chick_breed=chick_breed,
                quantity=quantity,
                chick_period=chick_period,
                feed_taken=feed_taken,
                payment_terms=payment_terms,
                received_through=received_through,
                # Assuming the logged-in user is the creator
                created_by=request.user  
            )

            try:
                # Validate and save the instance
                chick_request.full_clean()  # Runs the clean method including custom validations
                chick_request.save()
                messages.success(request, 'Chick request submitted successfully!')
                return redirect('salesagentdashboard')  # Redirect to dashboard after success
            except ValidationError as e:
                messages.error(request, '\n'.join(e.messages))  # Display validation errors
                return redirect('add_chick_request')

    # GET request: Render the form with farmer options
        farmers = Customer.objects.all()  # Fetch all farmers for the dropdown
        return render(request, '1addChickRequests.html', {'farmers': farmers})

def AddFeedRequest(request):
    return render(request, '1addFeedRequest.html')

def RegisterFarmer(request):
    return render(request, '1registerfarmer.html')

def AddChickRequest(request):
    return render(request, '1addChickRequests.html') 

def AddFeedRequest(request):
    return render(request, '1addFeedRequest.html')

def ViewSalesAgentChickRequests(request):
    return render(request, '1viewchickrequests.html')

def ViewSalesAgentFeedRequests(request):
    return render(request, '1viewfeedrequests.html')


def Logout(request):
    logout(request)
    return redirect('/')
   








