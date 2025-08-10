from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.core.exceptions import PermissionDenied
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm


# Create your views here.
# Landing page
def indexpage(request):
    # Example data – latest 10 chick requests (safe even if none exist)
    details = ChickRequest.objects.order_by('-id')[:10]
    return render(request, 'index.html', {'details': details})

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
            return redirect('login')
    #in case there is no data coming from the UserCreation form, direct to the signup.html page   
    else:
        form_data = UserCreation()
    return render(request, 'signup.html', {'form_data': form_data})

def Login(request):
    # If already authenticated send to their dashboard
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return _redirect_by_role(user)
        # invalid: surface error message
        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html', {'form': form, 'title': 'Login'})


def _redirect_by_role(user):
    if getattr(user, 'role', None) == 'sales_agent':
        return redirect('salesagentdashboard')
    if getattr(user, 'role', None) == 'manager':
        return redirect('Managersdashboard')
    return redirect('/')


def role_required(role):
    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if getattr(request.user, 'role', None) != role:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


#For the Managers

@role_required('manager')
def Managersdashboard(request):
    total_users = UserProfile.objects.count()
    chick_stock = ChickStock.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0
    feed_stock = FeedStock.objects.aggregate(total=Sum('feed_quantity'))['total'] or 0
    request_stats = ChickRequest.objects.values('status').annotate(c=Count('id'))
    stats_map = {r['status']: r['c'] for r in request_stats}
    completed_requests = stats_map.get('completed', 0)
    approved_requests = stats_map.get('approved', 0)
    pending_requests = stats_map.get('pending', 0)
    rejected_requests = stats_map.get('rejected', 0)
    total_sales = Sale.objects.count()
    deliveries_made = ChickRequest.objects.filter(delivered=True).count()
    pending_deliveries = ChickRequest.objects.filter(status='approved', delivered=False).count()
    farmers_with_feeds = FeedAllocation.objects.values('chick_request__farmer').distinct().count()
    farmers_paid = FeedAllocation.objects.filter(payment_status='paid').count()
    pending_payments = FeedAllocation.objects.filter(payment_status='pending').count()
    context = {
        'total_users': total_users,
        'chick_stock': chick_stock,
        'feed_stock': feed_stock,
        'completed_requests': completed_requests,
        'approved_requests': approved_requests,
        'pending_requests': pending_requests,
        'rejected_requests': rejected_requests,
        'total_sales': total_sales,
        'deliveries_made': deliveries_made,
        'pending_deliveries': pending_deliveries,
        'farmers_with_feeds': farmers_with_feeds,
        'farmers_paid': farmers_paid,
        'pending_payments': pending_payments,
    }
    return render(request, 'managersdashboard.html', context)

@role_required('manager')
def ViewChickRequests(request):
    requests_qs = ChickRequest.objects.select_related('farmer').order_by('-request_date')[:200]
    return render(request, 'viewChickrequests.html', {'requests': requests_qs})

@role_required('manager')
def ViewFeedRequests(request):
    feed_allocs = FeedAllocation.objects.select_related('chick_request', 'chick_request__farmer').order_by('-id')[:200]
    return render(request, 'viewFeedAllocations.html', {'allocations': feed_allocs})

@role_required('manager')
def FarmerReview(request):
    requests = ChickRequest.objects.select_related('farmer').order_by('-request_date')
    return render(request, 'farmerReview.html', {'requests': requests})

@role_required('manager')
def Approverequest(request):
    return render(request, 'approveRequest.html')


@role_required('manager')
def FarmerRecords(request):
    farmers = Customer.objects.order_by('-registration_date')[:500]
    return render(request, 'farmerRecords.html', {'farmers': farmers})

@role_required('manager')
def chickStock(request):
    chick_stocks = ChickStock.objects.order_by('batch_name')
    return render(request, 'chickStock.html', {'chick_stocks': chick_stocks})

@role_required('manager')
def feedStock(request):
    feed_stocks = FeedStock.objects.order_by('stock_name')
    return render(request, 'feedStock.html', {'feed_stocks': feed_stocks})

@role_required('manager')
def UpdateChickStock(request, stock_id=None):
    # Try to get existing stock if ID is provided
    chickstock = None
    if stock_id:
        try:
            chickstock = ChickStock.objects.get(id=stock_id)
        except ChickStock.DoesNotExist:
            messages.error(request, "Stock not found!")
            return redirect('/chickstock/')
    
    # Handle form submission
    if request.method == 'POST':
        # Get form data
        batch_name = request.POST.get('batch_name')
        chick_type = request.POST.get('chick_type')
        chick_breed = request.POST.get('chick_breed')
        chick_age = request.POST.get('chick_age')
        chick_price = request.POST.get('chick_price')
        stock_quantity = request.POST.get('stock_quantity')
        
        try:
            # Check if this batch already exists
            if chickstock:  # Editing existing stock
                existing_stock = chickstock
            else:
                existing_stock = ChickStock.objects.filter(batch_name=batch_name).first()
            
            if existing_stock:
                # Update existing stock
                existing_stock.batch_name = batch_name
                existing_stock.chick_type = chick_type
                existing_stock.chick_breed = chick_breed
                existing_stock.chick_age = chick_age
                existing_stock.chick_price = chick_price
                existing_stock.stock_quantity = stock_quantity
                existing_stock.save()
                messages.success(request, f"Stock '{batch_name}' updated successfully!")
            else:
                # Create new stock entry
                new_stock = ChickStock(
                    batch_name=batch_name,
                    chick_type=chick_type,
                    chick_breed=chick_breed,
                    chick_age=chick_age,
                    chick_price=chick_price,
                    stock_quantity=stock_quantity
                )
                new_stock.save()
                messages.success(request, f"New stock '{batch_name}' added successfully!")
            
            # Redirect to the stock listing page
            return redirect('/chickstock/')
        
        except Exception as e:
            # Handle errors
            messages.error(request, f"Error updating stock: {str(e)}")
            
            # Re-populate the form with submitted values
            form_data = type('', (), {})()
            form_data.batch_name = batch_name
            form_data.chick_type = chick_type
            form_data.chick_breed = chick_breed
            form_data.chick_age = chick_age
            form_data.chick_price = chick_price
            form_data.stock_quantity = stock_quantity
            return render(request, 'updateChickStock.html', {'chickstock': form_data})
    
    # For GET requests
    if not chickstock:
        # Show empty form for new stock
        class EmptyChickStock:
            def __init__(self):
                self.batch_name = ""
                self.chick_type = ""
                self.chick_breed = ""
                self.chick_age = ""
                self.chick_price = ""
                self.stock_quantity = ""
        
        chickstock = EmptyChickStock()
    
    return render(request, 'updateChickStock.html', {'chickstock': chickstock})

@role_required('manager')
def UpdateFeedStock(request):
    return render(request, 'updateFeedStock.html')

@role_required('manager')
def Reports(request):
    # Get various statistics for the reports page
    total_sales = Sale.objects.count()
    total_chick_requests = ChickRequest.objects.count()
    total_feed_allocations = FeedAllocation.objects.count()
    total_farmers = Customer.objects.count()
    
    # Get pending items
    pending_chick_requests = ChickRequest.objects.filter(status='pending').count()
    pending_feed_payments = FeedAllocation.objects.filter(payment_status='pending').count()
    
    # Get low stock items (less than 100 chicks or 50 bags of feed)
    low_stock_chicks = ChickStock.objects.filter(stock_quantity__lt=100).count()
    low_stock_feeds = FeedStock.objects.filter(feed_quantity__lt=50).count()
    low_stock_items = low_stock_chicks + low_stock_feeds
    
    # Get latest dates
    last_chick_request = ChickRequest.objects.order_by('-request_date').first()
    last_feed_allocation = FeedAllocation.objects.order_by('-id').first()
    last_stock_update = ChickStock.objects.order_by('-updated_at').first()
    
    context = {
        'total_sales': total_sales,
        'total_chick_requests': total_chick_requests,
        'total_feed_allocations': total_feed_allocations,
        'total_farmers': total_farmers,
        'pending_chick_requests': pending_chick_requests,
        'pending_feed_payments': pending_feed_payments,
        'low_stock_items': low_stock_items,
        'last_chick_request_date': last_chick_request.request_date.date() if last_chick_request else None,
        'last_feed_allocation_date': last_feed_allocation.id if last_feed_allocation else None,
        'last_stock_update': last_stock_update.updated_at.date() if last_stock_update else None,
    }
    return render(request, 'reports.html', context)

@role_required('manager')
def Sales(request):
    sales = Sale.objects.select_related('chick_request__farmer', 'recorded_by').order_by('-created_at')
    return render(request, 'sales.html', {'sales': sales})



@role_required('manager')
def DeleteRequest(request):
    return render(request, 'deleteRequest.html')




#For the Sales Agents
@role_required('sales_agent')
def SalesAgentdashboard(request):
    my_requests = ChickRequest.objects.filter(created_by=request.user)
    status_counts = my_requests.values('status').annotate(c=Count('id'))
    sc_map = {s['status']: s['c'] for s in status_counts}
    total_my_requests = my_requests.count()
    total_chicks_requested = my_requests.aggregate(total=Sum('quantity'))['total'] or 0
    delivered = my_requests.filter(delivered=True).count()
    context = {
        'total_my_requests': total_my_requests,
        'total_chicks_requested': total_chicks_requested,
        'my_pending': sc_map.get('pending', 0),
        'my_approved': sc_map.get('approved', 0),
        'my_rejected': sc_map.get('rejected', 0),
        'my_completed': sc_map.get('completed', 0),
        'delivered': delivered,
    }
    return render(request, '1salesAgentdashboard.html', context)

@role_required('sales_agent')
def AddChickRequest(request):
    if request.method == 'POST':
        farmer_id = request.POST.get('farmer')
        farmer = get_object_or_404(Customer, id=farmer_id)
        chick_request = ChickRequest(
            farmer=farmer,
            chick_request_id=request.POST.get('chick_request_id'),
            farmer_type=request.POST.get('farmer_type'),
            chick_type=request.POST.get('chick_type'),
            chick_breed=request.POST.get('chick_breed'),
            quantity=request.POST.get('quantity'),
            chick_period=request.POST.get('chick_period'),
            feed_taken=request.POST.get('feed_taken') == 'True',
            payment_terms=request.POST.get('payment_terms'),
            received_through=request.POST.get('received_through'),
            created_by=request.user
        )
        try:
            chick_request.full_clean()
            chick_request.save()
            messages.success(request, 'Chick request submitted successfully!')
            return redirect('salesagentdashboard')
        except Exception as e:
            messages.error(request, str(e))
    farmers = Customer.objects.all()
    return render(request, '1addChickRequests.html', {'farmers': farmers})

@role_required('sales_agent')
def AddFeedRequest(request):
    # Need chick requests belonging to this agent (approved or pending?) Use own requests
    chick_requests = ChickRequest.objects.filter(created_by=request.user)
    if request.method == 'POST':
        try:
            feed_allocation = FeedAllocation(
                feed_request_id=request.POST.get('feed_request_id'),
                feed_name=request.POST.get('feed_name') or request.POST.get('feed_type'),
                feed_type=request.POST.get('feed_type'),
                feed_brand=request.POST.get('feed_brand'),
                chick_request=get_object_or_404(ChickRequest, id=request.POST.get('chick_request')),
                bags_allocated=request.POST.get('bags_allocated') or 0,
                amount_due=request.POST.get('amount_due') or 0,
                payment_due_date=request.POST.get('payment_due_date') or None,
                payment_status=request.POST.get('payment_status') or 'pending'
            )
            feed_allocation.full_clean()
            feed_allocation.save()
            messages.success(request, 'Feed request submitted successfully!')
            return redirect('salesagentdashboard')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, '1addFeedRequest.html', {'chick_requests': chick_requests})

@role_required('sales_agent')
def RegisterFarmer(request):
    if request.method == 'POST':
        # basic creation of user+customer
        try:
            username = request.POST.get('farmer_id')
            # create user profile with farmer role
            user = UserProfile.objects.create_user(
                username=username,
                password=username,  # initial password (could be improved)
                role='farmer'
            )
            customer = Customer(
                user=user,
                farmer_id=request.POST.get('farmer_id'),
                farmer_name=request.POST.get('farmer_name'),
                date_of_birth=request.POST.get('date_of_birth'),
                age=request.POST.get('age') or 0,
                gender=request.POST.get('gender'),
                location=request.POST.get('location'),
                nin=request.POST.get('nin'),
                phone_number=request.POST.get('phone_number'),
                recommender_name=request.POST.get('recommender_name'),
                recommender_nin=request.POST.get('recommender_nin'),
                recommender_tel=request.POST.get('recommender_tel'),
                registered_by=request.user.username
            )
            customer.full_clean()
            customer.save()
            messages.success(request, 'Farmer registered successfully!')
            return redirect('salesagentdashboard')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, '1registerfarmer.html')

# duplicate duplicate definitions removed above

@role_required('sales_agent')
def ViewSalesAgentChickRequests(request):
    my_requests = ChickRequest.objects.filter(created_by=request.user).select_related('farmer').order_by('-request_date')
    return render(request, '1viewchickrequests.html', {'requests': my_requests})

@role_required('sales_agent')
def ViewSalesAgentFeedRequests(request):
    my_feed = FeedAllocation.objects.filter(chick_request__created_by=request.user).select_related('chick_request', 'chick_request__farmer')
    return render(request, '1viewfeedrequests.html', {'allocations': my_feed})


def Logout(request):
    logout(request)
    return redirect('/')
   








