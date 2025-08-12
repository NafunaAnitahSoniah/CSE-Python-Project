from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.http import HttpResponse
from datetime import datetime
from django.core.exceptions import PermissionDenied
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction


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
    # Total sales amount = feed (approved: bags*selling_price) + chicks (approved: qty*price)
    feed_total = FeedAllocation.objects.filter(status='approved').aggregate(
        total=Sum(F('bags_allocated') * F('feed_stock__selling_price'))
    )['total'] or 0
    # Latest price per type/breed: use the most recent updated stock entry
    # For aggregate simplicity, iterate in Python (small datasets typical for dashboard)
    chick_total = 0
    for req in ChickRequest.objects.filter(status='approved').select_related('farmer'):
        price = ChickStock.objects.filter(
            chick_type=req.chick_type,
            chick_breed=req.chick_breed
        ).order_by('-updated_at').values_list('chick_price', flat=True).first() or 1650
        chick_total += int(req.quantity or 0) * int(price)
    total_sales = feed_total + chick_total
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
    feed_allocs = FeedAllocation.objects.select_related('chick_request', 'chick_request__farmer', 'feed_stock').order_by('-id')[:200]
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
    # chick_age removed from form per requirements; keep existing value when editing
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
                # preserve existing chick_age
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
                    chick_age=1,  # default minimal age since field exists in model
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
            # age not editable in UI
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
                self.chick_age = 1
                self.chick_price = ""
                self.stock_quantity = ""
        
        chickstock = EmptyChickStock()
    
    return render(request, 'updateChickStock.html', {'chickstock': chickstock})

@role_required('manager')
def UpdateFeedStock(request, stock_id=None):
    # Try to get existing stock if ID is provided
    feed_stock = None
    if stock_id:
        try:
            feed_stock = FeedStock.objects.get(id=stock_id)
        except FeedStock.DoesNotExist:
            messages.error(request, 'Feed stock not found.')
            return redirect('Feedstock')
    
    if request.method == 'POST':
        try:
            if feed_stock:
                # Update existing feed stock
                feed_stock.stock_name = request.POST.get('stock_name')
                feed_stock.feed_name = request.POST.get('feed_name')
                feed_stock.feed_type = request.POST.get('feed_type')
                feed_stock.feed_brand = request.POST.get('feed_brand')
                feed_stock.feed_quantity = request.POST.get('feed_quantity')
                feed_stock.expiry_date = request.POST.get('expiry_date')
                feed_stock.purchase_price = request.POST.get('purchase_price')
                feed_stock.selling_price = request.POST.get('selling_price')
                feed_stock.supplier = request.POST.get('supplier')
                feed_stock.supplier_contact = request.POST.get('supplier_contact')
            else:
                # Create new feed stock
                feed_stock = FeedStock(
                    stock_name=request.POST.get('stock_name'),
                    feed_name=request.POST.get('feed_name'),
                    feed_type=request.POST.get('feed_type'),
                    feed_brand=request.POST.get('feed_brand'),
                    feed_quantity=request.POST.get('feed_quantity'),
                    expiry_date=request.POST.get('expiry_date'),
                    purchase_price=request.POST.get('purchase_price'),
                    selling_price=request.POST.get('selling_price'),
                    supplier=request.POST.get('supplier'),
                    supplier_contact=request.POST.get('supplier_contact')
                )
            
            feed_stock.full_clean()
            feed_stock.save()
            
            if stock_id:
                messages.success(request, 'Feed stock updated successfully!')
            else:
                messages.success(request, 'Feed stock added successfully!')
            return redirect('Feedstock')
        except Exception as e:
            messages.error(request, str(e))
    
    return render(request, 'updateFeedStock.html', {'feed_stock': feed_stock})

@role_required('manager')
def Reports(request):
    # Get various statistics for the reports page
    # Total sales amount for reports (same calc as dashboard)
    feed_total = FeedAllocation.objects.filter(status='approved').aggregate(
        total=Sum(F('bags_allocated') * F('feed_stock__selling_price'))
    )['total'] or 0
    chick_total = 0
    for req in ChickRequest.objects.filter(status='approved'):
        price = ChickStock.objects.filter(
            chick_type=req.chick_type,
            chick_breed=req.chick_breed
        ).order_by('-updated_at').values_list('chick_price', flat=True).first() or 1650
        chick_total += int(req.quantity or 0) * int(price)
    total_sales = feed_total + chick_total
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
    'last_feed_allocation_date': getattr(last_feed_allocation, 'payment_due_date', None) if last_feed_allocation else None,
        'last_stock_update': last_stock_update.updated_at.date() if last_stock_update else None,
    }
    return render(request, 'reports.html', context)

@role_required('manager')
def Sales(request):
    # Filters: optional start/end date (YYYY-MM-DD)
    start = request.GET.get('start')
    end = request.GET.get('end')
    def parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except Exception:
            return None
    start_date = parse_date(start)
    end_date = parse_date(end)

    # Feed sales rows: approved allocations with amounts = bags * selling_price
    feed_qs = FeedAllocation.objects.filter(status='approved').select_related('chick_request__farmer', 'feed_stock').order_by('-id')
    if start_date:
        feed_qs = feed_qs.filter(chick_request__request_date__date__gte=start_date)
    if end_date:
        feed_qs = feed_qs.filter(chick_request__request_date__date__lte=end_date)
    feed_rows = []
    feed_total = 0
    for a in feed_qs:
        price = getattr(a.feed_stock, 'selling_price', 0) or 0
        amount = int(a.bags_allocated or 0) * int(price)
        feed_total += amount
        feed_rows.append({
            'feed_request_id': a.feed_request_id,
            'req_id': a.chick_request.chick_request_id,
            'farmer': a.chick_request.farmer.farmer_name,
            'feed_name': a.feed_name,
            'brand': a.feed_brand,
            'bags': a.bags_allocated,
            'unit_price': price,
            'amount': amount,
            'date': a.chick_request.request_date,
        })

    # Chick sales rows: approved chick requests with amount = qty * price (latest for type/breed)
    chick_qs = ChickRequest.objects.filter(status='approved').select_related('farmer').order_by('-request_date')
    if start_date:
        chick_qs = chick_qs.filter(request_date__date__gte=start_date)
    if end_date:
        chick_qs = chick_qs.filter(request_date__date__lte=end_date)
    chick_rows = []
    chick_total = 0
    for r in chick_qs:
        price = ChickStock.objects.filter(
            chick_type=r.chick_type,
            chick_breed=r.chick_breed
        ).order_by('-updated_at').values_list('chick_price', flat=True).first() or 1650
        amount = int(r.quantity or 0) * int(price)
        chick_total += amount
        chick_rows.append({
            'req_id': r.chick_request_id,
            'farmer': r.farmer.farmer_name,
            'type': r.chick_type,
            'breed': r.chick_breed,
            'qty': r.quantity,
            'unit_price': price,
            'amount': amount,
            'date': r.request_date,
        })

    total_sales = feed_total + chick_total

    return render(request, 'sales.html', {
        'feed_rows': feed_rows,
        'feed_total': feed_total,
        'chick_rows': chick_rows,
        'chick_total': chick_total,
        'total_sales': total_sales,
        'start': start or '',
        'end': end or '',
    })



@role_required('manager')
def DeleteRequest(request):
    return render(request, 'deleteRequest.html')

@role_required('manager')
def ApproveFeedRequest(request, request_id):
    try:
        feed_allocation = FeedAllocation.objects.select_related('feed_stock').get(id=request_id)

        if request.method == 'POST':
            action = request.POST.get('action')

            if action not in ('approve', 'reject'):
                messages.error(request, 'Invalid action.')
                return redirect('Viewfeedrequests')

            with transaction.atomic():
                if action == 'approve':
                    # Ensure linked stock and enough quantity
                    stock = feed_allocation.feed_stock
                    bags = int(feed_allocation.bags_allocated or 0)
                    if stock and (stock.feed_quantity or 0) >= bags:
                        # Deduct inventory
                        stock.feed_quantity = (stock.feed_quantity or 0) - bags
                        stock.save(update_fields=['feed_quantity'])
                        # Update allocation status only (do not force payment status)
                        feed_allocation.status = 'approved'
                        feed_allocation.save(update_fields=['status'])
                        messages.success(request, 'Feed request approved successfully!')
                    else:
                        messages.error(request, 'Insufficient stock to approve this request.')
                        return redirect('Viewfeedrequests')
                else:  # reject
                    feed_allocation.status = 'rejected'
                    feed_allocation.payment_status = 'rejected'
                    feed_allocation.save(update_fields=['status', 'payment_status'])
                    messages.success(request, 'Feed request rejected successfully!')

        return redirect('Viewfeedrequests')

    except FeedAllocation.DoesNotExist:
        messages.error(request, 'Feed request not found.')
        return redirect('Viewfeedrequests')




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
def RegisterFarmer(request):
    if request.method == 'POST':
        try:
            # Generate a unique username for the farmer
            import uuid
            username = f"farmer_{uuid.uuid4().hex[:8]}"
            
            # Create user profile with farmer role
            user = UserProfile.objects.create_user(
                username=username,
                password=username,  # initial password (could be improved)
                role='farmer'
            )
            
            # Create customer record (farmer_id will be auto-generated)
            customer = Customer(
                user=user,
                farmer_name=request.POST.get('farmer_name'),
                date_of_birth=request.POST.get('date_of_birth'),
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
            messages.success(request, f'Farmer registered successfully! Farmer ID: {customer.farmer_id}')
            return redirect('salesagentdashboard')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, '1registerfarmer.html')

@role_required('sales_agent')
def AddChickRequest(request):
    if request.method == 'POST':
        try:
            farmer_id = request.POST.get('farmer')
            farmer = get_object_or_404(Customer, id=farmer_id)
            
            chick_request = ChickRequest(
                farmer=farmer,
                farmer_type=request.POST.get('farmer_type'),
                chick_type=request.POST.get('chick_type'),
                chick_breed=request.POST.get('chick_breed'),
                quantity=request.POST.get('quantity'),
                chick_period=1,  # field kept in model; default to 1 day since input was removed
                feed_taken=request.POST.get('feed_taken') == 'True',
                feed_name=request.POST.get('feed_name') or None,
                payment_terms=request.POST.get('payment_terms'),
                received_through=request.POST.get('received_through'),
                created_by=request.user
            )
            chick_request.full_clean()
            chick_request.save()
            messages.success(request, f'Chick request submitted successfully! Request ID: {chick_request.chick_request_id}')
            return redirect('salesagentdashboard')
        except Exception as e:
            messages.error(request, str(e))
    
    # Get all farmers for the dropdown
    farmers = Customer.objects.all().order_by('farmer_name')
    # Approved feeds for this agent
    approved_feeds = FeedAllocation.objects.filter(
        chick_request__created_by=request.user,
        status='approved'
    ).order_by('-id')
    # Build stock counts for dynamic breed display
    def count_for(t, b):
        return sum(s.stock_quantity or 0 for s in ChickStock.objects.filter(chick_type=t, chick_breed=b))
    stock_counts = {
        'layer': {'local': count_for('layer', 'local'), 'exotic': count_for('layer', 'exotic')},
        'broiler': {'local': count_for('broiler', 'local'), 'exotic': count_for('broiler', 'exotic')},
    }
    return render(request, '1addChickRequests.html', {
        'farmers': farmers,
        'approved_feeds': approved_feeds,
        'stock_counts': stock_counts,
    })

@role_required('sales_agent')
def AddFeedRequest(request):
    # Get chick requests belonging to this agent (approved or pending)
    chick_requests = ChickRequest.objects.filter(created_by=request.user, status__in=['approved', 'pending']).select_related('farmer')
    
    # Get available feed stock
    feed_stocks = FeedStock.objects.filter(feed_quantity__gt=0).order_by('feed_name')
    
    if request.method == 'POST':
        try:
            feed_stock_id = request.POST.get('feed_stock') or None
            feed_stock = FeedStock.objects.filter(id=feed_stock_id).first() if feed_stock_id else None
            
            feed_allocation = FeedAllocation(
                feed_stock=feed_stock,
                feed_name=feed_stock.feed_name,
                feed_type=feed_stock.feed_type,
                feed_brand=feed_stock.feed_brand,
                chick_request=get_object_or_404(ChickRequest, id=request.POST.get('chick_request')),
                bags_allocated=request.POST.get('bags_allocated'),
                amount_due=request.POST.get('amount_due'),
                payment_due_date=request.POST.get('payment_due_date'),
                payment_status=request.POST.get('payment_status')
            )
            feed_allocation.full_clean()
            feed_allocation.save()
            messages.success(request, f'Feed request submitted successfully! Feed Request ID: {feed_allocation.feed_request_id}')
            return redirect('salesagentdashboard')
        except Exception as e:
            messages.error(request, str(e))
    
    return render(request, '1addFeedRequest.html', {
        'chick_requests': chick_requests,
        'feed_stocks': feed_stocks
    })

@role_required('sales_agent')
def ViewSalesAgentChickRequests(request):
    my_requests = ChickRequest.objects.filter(created_by=request.user).select_related('farmer').order_by('-request_date')
    return render(request, '1viewchickrequests.html', {'chick_requests': my_requests})

@role_required('sales_agent')
def ViewSalesAgentFeedRequests(request):
    my_feed = FeedAllocation.objects.filter(chick_request__created_by=request.user).select_related('chick_request', 'chick_request__farmer', 'feed_stock').order_by('-id')
    return render(request, '1viewfeedrequests.html', {'allocations': my_feed})


@role_required('manager')
def ApproveChickRequest(request, request_id: int):
    """Approve or reject a chick request; on approval, deduct chick stock by type/breed."""
    req = get_object_or_404(ChickRequest, id=request_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action not in ('approve', 'reject'):
            messages.error(request, 'Invalid action.')
            return redirect('Viewchickrequests')
        if action == 'reject':
            req.status = 'rejected'
            req.save(update_fields=['status'])
            messages.success(request, 'Chick request rejected successfully!')
            return redirect('Viewchickrequests')
        # approve
        with transaction.atomic():
            # Sum available stock for the requested type/breed
            stocks = list(ChickStock.objects.select_for_update().filter(
                chick_type=req.chick_type,
                chick_breed=req.chick_breed
            ).order_by('-stock_quantity'))
            needed = int(req.quantity or 0)
            available = sum(s.stock_quantity or 0 for s in stocks)
            if available < needed:
                messages.error(request, 'Insufficient chick stock for the requested type/breed.')
                return redirect('Viewchickrequests')
            remaining = needed
            for s in stocks:
                if remaining <= 0:
                    break
                take = min(remaining, s.stock_quantity or 0)
                s.stock_quantity = (s.stock_quantity or 0) - take
                s.save(update_fields=['stock_quantity'])
                remaining -= take
            req.status = 'approved'
            req.approved_on = timezone.now()
            req.save(update_fields=['status', 'approved_on'])
            messages.success(request, 'Chick request approved and stock updated!')
    return redirect('Viewchickrequests')


# --- TXT Export endpoints (manager) ---
@role_required('manager')
def export_sales_txt(request):
    # Build combined sales export from approved feed allocations and chick requests
    lines = ['TYPE\tREQ_ID\tFARMER\tITEM\tQTY/BAGS\tUNIT_PRICE\tAMOUNT\tDATE\n']
    # Feed
    for a in FeedAllocation.objects.filter(status='approved').select_related('chick_request__farmer', 'feed_stock').order_by('id'):
        price = getattr(a.feed_stock, 'selling_price', 0) or 0
        amount = int(a.bags_allocated or 0) * int(price)
        lines.append(f"FEED\t{a.chick_request.chick_request_id}\t{a.chick_request.farmer.farmer_name}\t{a.feed_name}\t{a.bags_allocated}\t{price}\t{amount}\t{a.chick_request.request_date.date()}\n")
    # Chicks
    for r in ChickRequest.objects.filter(status='approved').select_related('farmer').order_by('request_date'):
        price = ChickStock.objects.filter(chick_type=r.chick_type, chick_breed=r.chick_breed).order_by('-updated_at').values_list('chick_price', flat=True).first() or 1650
        amount = int(r.quantity or 0) * int(price)
        lines.append(f"CHICKS\t{r.chick_request_id}\t{r.farmer.farmer_name}\t{r.chick_type}/{r.chick_breed}\t{r.quantity}\t{price}\t{amount}\t{r.request_date.date()}\n")
    resp = HttpResponse(''.join(lines), content_type='text/plain')
    resp['Content-Disposition'] = 'attachment; filename="sales.txt"'
    return resp

@role_required('manager')
def export_chick_requests_txt(request):
    header = 'REQ_ID\tFARMER\tTYPE\tBREED\tQTY\tSTATUS\tDATE\n'
    rows = [
        f"{r.chick_request_id}\t{r.farmer.farmer_name}\t{r.chick_type}\t{r.chick_breed}\t{r.quantity}\t{r.status}\t{r.request_date.date()}\n"
        for r in ChickRequest.objects.select_related('farmer').order_by('request_date')
    ]
    resp = HttpResponse(header + ''.join(rows), content_type='text/plain')
    resp['Content-Disposition'] = 'attachment; filename="chick_requests.txt"'
    return resp

@role_required('manager')
def export_feed_allocations_txt(request):
    header = 'FEED_ID\tREQ_ID\tFEED\tBAGS\tSTATUS\tPAYMENT\n'
    rows = [
        f"{a.feed_request_id}\t{a.chick_request.chick_request_id}\t{a.feed_name}\t{a.bags_allocated}\t{a.status}\t{a.payment_status}\n"
        for a in FeedAllocation.objects.select_related('chick_request').order_by('id')
    ]
    resp = HttpResponse(header + ''.join(rows), content_type='text/plain')
    resp['Content-Disposition'] = 'attachment; filename="feed_allocations.txt"'
    return resp

@role_required('manager')
def export_chick_stock_txt(request):
    header = 'BATCH\tTYPE\tBREED\tAGE\tPRICE\tQTY\n'
    rows = [
        f"{s.batch_name}\t{s.chick_type}\t{s.chick_breed}\t{s.chick_age}\t{s.chick_price}\t{s.stock_quantity}\n"
        for s in ChickStock.objects.order_by('batch_name')
    ]
    resp = HttpResponse(header + ''.join(rows), content_type='text/plain')
    resp['Content-Disposition'] = 'attachment; filename="chick_stock.txt"'
    return resp

@role_required('manager')
def export_feed_stock_txt(request):
    header = 'STOCK\tFEED\tTYPE\tBRAND\tQTY\tPRICE\n'
    rows = [
        f"{s.stock_name}\t{s.feed_name}\t{s.feed_type}\t{s.feed_brand}\t{s.feed_quantity}\t{s.selling_price}\n"
        for s in FeedStock.objects.order_by('stock_name')
    ]
    resp = HttpResponse(header + ''.join(rows), content_type='text/plain')
    resp['Content-Disposition'] = 'attachment; filename="feed_stock.txt"'
    return resp

@role_required('manager')
def export_farmers_txt(request):
    header = 'FARMER_ID\tNAME\tGENDER\tAGE\tPHONE\tLOCATION\n'
    rows = [
        f"{c.farmer_id}\t{c.farmer_name}\t{c.gender}\t{c.age}\t{c.phone_number}\t{c.location}\n"
        for c in Customer.objects.order_by('farmer_id')
    ]
    resp = HttpResponse(header + ''.join(rows), content_type='text/plain')
    resp['Content-Disposition'] = 'attachment; filename="farmers.txt"'
    return resp


def Logout(request):
    logout(request)
    return redirect('/')

    return render(request, '1viewfeedrequests.html', {'allocations': my_feed})





def Logout(request):

    logout(request)

    return redirect('/')


