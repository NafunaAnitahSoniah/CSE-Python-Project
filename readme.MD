models
class: chicks stock
proprty;
stock Name: 'batch name' (characterfield)
date: (date automatic)
chick breed(characterfield) local/exotic
chick type(characterfield) layers/broilers
quantity(intergerfield)
chicks period in days(age)
stock authoriser

class: price
property;
price
class: feeds stock
property;
name
date
quantity of feeds
type of feeds
brand of feeds
unit price
supplier 
supplier contact
buying price
selling price

class: customer
propertt;
farmer's name(all at once) 
farmer's age(18-30)
farmer gender
type of farmer(new/returning)
farmer nin
farmer tel
recommender's name
recommender's nin
recoommender's tel

class: application for chicks(chics_request)
property; 
farmer's name(all at once) foreign key of the class customer
type of chic
type of breed
quantity
status(pending/approved/rejected)
date
took feeds(yes/no) radio button for yes/no
chick period in days
delivery status(if farmer picked the chicks) (yes/no)

MODELS
from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class chick_stock(models.Model):
    stock_name = models.CharField(max_length=50)
    chick_type = models.CharField(max_length=15)
    chick_breed = models.CharField(max_length=15)
    chick_price = models.PositiveIntegerField(default=1650)
    stock_quantity = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)
    stock_taker = models.CharField(max_length=50)

class feed_stock(models.Model):
    feed_name = models.CharField(max_length=50)
    feed_type = models.CharField(max_length=25)
    feed_brand = models.CharField(max_length=25)
    feed_quantity = models.IntegerField()
    purchase_amount = models.IntegerField(blank=True)
    selling_amount = models.IntegerField()
    supplier = models.TextField()
    supplier_contact = models.CharField(max_length=15, unique=True)
    date = models.DateField(auto_now_add=True)
class customer(models.Model):
    farmer_id = models.ForeignKey(User, on_delete= models.CASCADE)
    farmer_name = models.CharField(max_length=50)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    NIN = models.CharField(max_length=30)
    phone_number = models.CharField(15)
    recommender_name = models.TextField()
    recommender_NIN = models.CharField(max_length=30)
    recommender_tel = models.CharField(max_length=15)

class chick_request(models.Model):
    farmer_id = models.ForeignKey(User, on_delete= models.CASCADE)
    chick_type = models.CharField(max_length=15)
    chick_breed = models.CharField(max_length=15)
    quantity = models.PositiveIntegerField()
    chick_period = models.PositiveIntegerField()
    feed_taken = models.CharField(max_length=5)
    status = models.CharField(max_length=20)
    delivered = models.CharField(max_length=5)
    date = models.DateField(auto_now_add=True)

***
from django.db import models
from django.conf import settings #for ForeignKey to user
#Extending the super User class for us to create our own users
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone 

# Create your models here.
class UserprofileAbstractUser(): 
    is_salesagent = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    phone = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=30)
    username = models.CharField(max_length=30, unique=True)
    


    def __str__(self):
        return str(self.username)
    
#To create a table name called farmer users
    class Meta:
        db_table = "farmer_users"
        verbose_name = "User"
        verbose_name_plural = "Users"

class ChickStock(models.Model):
    batch_name = models.CharField(max_length=25, unique=True)
    chick_type = models.CharField(max_length=15, choices=[('layer', 'Layer'), ('broiler', 'Broiler')])
    chick_breed = models.CharField(max_length=15, choices=[('local', 'Local'), ('exotic', 'Exotic')])
    chick_age = models.PositiveIntegerField()
    chick_price = models.PositiveIntegerField(primary_key=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    updated = models.DateField(auto_now_add=True)
    stock_taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)


    def __str__(self):
        return f"{self.batch_name} - {self.chick_type} - {self.chick_breed}"

class FeedStock(models.Model):
    stock_name = models.CharField(max_length=25, unique=True)
    feed_name = models.CharField(max_length=25)
    feed_type = models.CharField(max_length=25)
    feed_brand = models.CharField(max_length=25)
    feed_quantity = models.PositiveIntegerField()
    expiry_date = models.DateField()
    purchase_price = models.PositiveIntegerField(blank=True)
    selling_price = models.PositiveIntegerField()
    supplier = models.TextField()
    supplier_contact = models.CharField(max_length=15, unique=True)
    updated = models.DateField(auto_now_add=True)


    def __str__(self):
        return self.feed_name

class Customer(models.Model):    
    farmer_name = models.CharField(max_length=50, on_delete= models.CASCADE)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(30)])
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    location = models.CharField(max_length=30)
    NIN = models.CharField(max_length=30, unique=True)
    phone_number = models.CharField(15)
    recommender_name = models.CharField(max_length=50)
    recommender_NIN = models.CharField(max_length=30)
    recommender_tel = models.CharField(max_length=15)
    registered_by = models.CharField(max_length=50)
    registration_date = models.DateField(auto_now_add=True)


    def __str__(self):
        return self.farmer_id 

class ChickRequest(models.Model):
    farmer = models.ForeignKey(Customer)
    chickRequest_id = models.CharField(max_length=15, unique=True)
    farmer_type = models.CharField(max_length=10, choices=[('starter', 'Starter'), ('returning', 'Returning')]) #starter/ returning
    chick_type = models.CharField(max_length=15, choices=[('layer', 'Layer'), ('broiler', 'Broiler')])
    chick_breed = models.CharField(max_length=15, choices=[('local', 'Local'), ('exotic', 'Exotic')])
    quantity = models.PositiveIntegerField()
    chick_period = models.PositiveIntegerField()
    feed_taken = models.CharField(max_length=5, choices=[('yes', 'Yes'), ('no', 'No')])
    payment_terms = models.CharField(choices=['MM', 'Visa', 'Cash'])
    request_date = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50)
    status = models.CharField(max_length=20, 
    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('completed', 'Completed')], default=('pending', 'Pending'))
    approved_on = models.DateField(null=True, blank=True)
    delivered = models.CharField(max_length=5)


    def __str__(self):
        return self.chickRequest_id
    
class FeedAllocation(models.Model):
    feed_requestID = models.CharField(max_length=15, unique=True)
    feed_name = models.CharField(max_length=25)
    feed_type = models.CharField(max_length=25)
    feed_brand = models.CharField(max_length=25)
    chick_request = models.ForeignKey(ChickRequest, on_delete= models.CASCADE)
    bags_allocated = models.PositiveIntegerField(default=2)
    amount_due = models.PositiveIntegerField()
    payment_due_date= models.DateField()  #2 months from allocation
    payment_status= models.CharField(max_length=20, choices=[('pending','Pending'), ('paid', 'Paid')], default=('pending', 'Pending'))

    def __str__(self):
        return self.feed_requestID 

***
FROM MY FORMS.PY
class UserProfileCreationForm(UserCreationForm):
    phone = forms.CharField(
        max_length=15,
        label="Phone Number",
        help_text="Enter a valid phone number (e.g., +256123456789).",
        validators=[
            forms.validators.RegexValidator(
                r'^\+?\d{10,15}$',
                'Enter a valid phone number.'
            )
        ]
    )
    title = forms.CharField(max_length=30, required=False, label="Title")

    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'phone', 'title', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'farmer'  # Default role for new registrations
        if commit:
            user.save()
        return user

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'farmer_id', 'farmer_name', 'date_of_birth', 'age', 'gender',
            'location', 'nin', 'phone_number', 'recommender_name',
            'recommender_nin', 'recommender_tel', 'registered_by'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(choices=[('M', 'Male'), ('F', 'Female')]),
            'registered_by': forms.Select()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter registered_by to sales agents or managers
        self.fields['registered_by'].queryset = UserProfile.objects.filter(
            role__in=['sales_agent', 'manager']
        )

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        age = cleaned_data.get('age')
        if date_of_birth and age:
            today = timezone.now().date()
            calculated_age = today.year - date_of_birth.year - (
                (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
            )
            if calculated_age != age:
                raise ValidationError('Age does not match date of birth.')
        return cleaned_data

class ChickRequestForm(forms.ModelForm):
    class Meta:
        model = ChickRequest
        fields = [
            'farmer_type', 'chick_type', 'chick_breed', 'quantity',
            'chick_period', 'feed_taken', 'payment_terms'
        ]
        widgets = {
            'farmer_type': forms.Select(choices=[('starter', 'Starter'), ('returning', 'Returning')]),
            'chick_type': forms.Select(choices=[('layer', 'Layer'), ('broiler', 'Broiler')]),
            'chick_breed': forms.Select(choices=[('local', 'Local'), ('exotic', 'Exotic')]),
            'feed_taken': forms.CheckboxInput(),
            'payment_terms': forms.Select(choices=[
                ('mobile_money', 'Mobile Money'),
                ('visa', 'Visa'),
                ('cash', 'Cash')
            ]),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.role == 'sales_agent':
            self.fields['farmer'] = forms.ModelChoiceField(
                queryset=Customer.objects.all(),
                label="Farmer",
                required=True
            )
        else:
            self.fields.pop('farmer', None)  # Farmers can't select farmer

    def clean(self):
        cleaned_data = super().clean()
        farmer_type = cleaned_data.get('farmer_type')
        quantity = cleaned_data.get('quantity')
        if farmer_type == 'starter' and quantity != 100:
            raise ValidationError('Starter farmers must request exactly 100 chicks.')
        if farmer_type == 'returning' and quantity > 500:
            raise ValidationError('Returning farmers cannot request more than 500 chicks.')
        return cleaned_data

some views

def role_required(*roles):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Access denied.')
            return redirect('home')
        return wrapper
    return decorator

def home(request):
    return render(request, 'core/home.html')

def signUp_user(request):
    if request.method == 'POST':
        user_form = UserProfileCreationForm(request.POST)
        customer_form = CustomerForm(request.POST)
        if user_form.is_valid() and customer_form.is_valid():
            user = user_form.save()
            customer = customer_form.save(commit=False)
            customer.user = user
            customer.full_clean()
            customer.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('/login')
    else:
        user_form = UserProfileCreationForm()
        customer_form = CustomerForm()
    return render(request, 'core/register.html', {
        'user_form': user_form,
        'customer_form': customer_form
    })

@login_required
@role_required('farmer', 'sales_agent')
def submit_request(request):
    if request.method == 'POST':
        form = ChickRequestForm(request.POST, user=request.user)
        if form.is_valid():
            chick_request = form.save(commit=False)
            if request.user.role == 'farmer':
                chick_request.farmer = get_object_or_404(Customer, user=request.user)
            else:  # Sales agent
                chick_request.farmer = form.cleaned_data['farmer']
            chick_request.chick_request_id = f"REQ{timezone.now().strftime('%Y%m%d%H%M%S')}"
            chick_request.created_by = request.user
            chick_request.full_clean()
            chick_request.save()
            if chick_request.feed_taken:
                feed = ChickStock.objects.first()  # Simplified; select appropriate feed
                FeedAllocation.objects.create(
                    feed_request_id=f"FEED{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    feed_name=feed.feed_name,
                    feed_type=feed.feed_type,
                    feed_brand=feed.feed_brand,
                    chick_request=chick_request,
                    amount_due=feed.selling_price * 2
                )
            messages.success(request, 'Request submitted successfully.')
            return redirect('farmer_dashboard' if request.user.role == 'farmer' else 'sales_dashboard')
    else:
        form = ChickRequestForm(user=request.user)
    return render(request, 'core/submit_request.html', {'form': form})

@login_required
@role_required('farmer')
def farmer_dashboard(request):
    customer = get_object_or_404(Customer, user=request.user)
    requests = ChickRequest.objects.filter(farmer=customer)
    return render(request, 'core/farmer_dashboard.html', {'requests': requests})

@login_required
@role_required('manager')
def manager_dashboard(request):
    stocks = ChickStock.objects.all()
    requests = ChickRequest.objects.filter(status='pending')
    return render(request, 'core/manager_dashboard.html', {'stocks': stocks, 'requests': requests})

@login_required
@role_required('manager')
def approve_request(request, request_id):
    chick_request = get_object_or_404(ChickRequest, chick_request_id=request_id)
    if request.method == 'POST':
        if 'approve' in request.POST:
            stock = ChickStock.objects.filter(chick_type=chick_request.chick_type, chick_breed=chick_request.chick_breed).first()
            if stock and stock.stock_quantity >= chick_request.quantity:
                stock.stock_quantity -= chick_request.quantity
                stock.save()
                chick_request.status = 'approved'
                chick_request.approved_on = timezone.now()
                chick_request.save()
                messages.success(request, 'Request approved.')
            else:
                messages.error(request, 'Insufficient stock.')
        elif 'reject' in request.POST:
            chick_request.status = 'rejected'
            chick_request.save()
            messages.success(request, 'Request rejected.')
        return redirect('manager_dashboard')
    return render(request, 'core/approve_request.html', {'request': chick_request})

@login_required
@role_required('sales_agent')
def sales_dashboard(request):
    requests = ChickRequest.objects.filter(Q(status='approved') | Q(status='completed'))
    return render(request, 'core/sales_dashboard.html', {'requests': requests})

@login_required
@role_required('sales_agent')
def complete_sale(request, request_id):
    chick_request = get_object_or_404(ChickRequest, chick_request_id=request_id)
    if chick_request.status == 'approved':
        Sale.objects.create(
            sale_id=f"SALE{timezone.now().strftime('%Y%m%d%H%M%S')}",
            chick_request=chick_request,
            total_amount=chick_request.quantity * 1650,
            recorded_by=request.user
        )
        chick_request.status = 'completed'
        chick_request.delivered = True
        chick_request.save()
        messages.success(request, 'Sale completed.')
    else:
        messages.error(request, 'Request not approved.')
    return redirect('sales_dashboard')


   #VIEW FOR INDEX.HTML PAGE
    def indexpage(request):
    details = Request.objects.all().order_by('-id')
    return render(request, 'index.html',{'details': details})

    HTML
    <main class="container my-5">
            <div class="card-block" >
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Farmer</th>
                                <th>Quantity</th>
                                <th>Date</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr >
                                <td class="text-xs-center">{{ details.farmer }}</td>
                                <td class="text-xs-center">{{ details.quantity }}</td>
                                <td class="text-xs-center">{{ details.date }}</td>
                                <td class="text-xs-center">{{ details.status }}</td>
                            </tr>
                        </tbody>
                    </table>

                </div>

            </div>
   
        </main>


Manager Dashboard Base Templatehtml

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manager Dashboard - Young4ChickS</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; display: flex; }
        .sidebar { width: 250px; background-color: #f8f9fa; padding: 20px; height: 100vh; }
        .navbar-brand img { width: 150px; }
        .nav { list-style: none; padding: 0; }
        .nav-item { margin: 10px 0; }
        .nav-link { text-decoration: none; color: #333; font-size: 16px; display: flex; align-items: center; }
        .nav-link i { margin-right: 10px; }
        .logout-btn { background-color: #d32f2f; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; font-weight: 500; width: 100%; margin-top: 20px; cursor: pointer; }
        .content { flex-grow: 1; padding: 20px; }
        .footer { background-color: #333; color: #fff; text-align: center; padding: 10px; position: fixed; bottom: 0; width: 100%; }
    </style>
</head>
<body>
    <div class="sidebar">
        <a class="navbar-brand" href="#">
            <img src="{% static 'images/logo.png' %}" alt="Young4ChickS Logo">
        </a>
        <ul class="nav">
            <li class="nav-item"><a class="nav-link" href="/"><i class="fas fa-home"></i>Home</a></li>
            <li class="nav-item"><a class="nav-link" href="/managersdashboard/"><i class="fas fa-list"></i>Managers Dash Board</a></li>
            <li class="nav-item"><a class="nav-link" href="/chickrequests/"><i class="fas fa-list"></i>View Chick Requests</a></li>
            <li class="nav-item"><a class="nav-link" href="/feedrequests/"><i class="fas fa-list"></i>View Feed Requests</a></li>
            <li class="nav-item"><a class="nav-link" href="/chickStock/"><i class="fas fa-chick"></i>Chick Stock</a></li>
            <li class="nav-item"><a class="nav-link" href="/feedStock/"><i class="fas fa-seedling"></i>Feed Stock</a></li>
            <li class="nav-item"><a class="nav-link" href="/farmerrecords/"><i class="fas fa-users"></i>Farmer Records</a></li>
            <li class="nav-item"><a class="nav-link" href="/sales/"><i class="fas fa-dollar-sign"></i>Sales</a></li>
            <li class="nav-item"><a class="nav-link" href="/reports/"><i class="fas fa-chart-bar"></i>Reports</a></li>
        </ul>
        <button class="logout-btn" onclick="window.location.href='/logout'">Logout</button>
    </div>
    <div class="content">
        <!-- Manager Dashboard Content Placeholder -->
        <h1>Manager Dashboard</h1>
        <p>Insert content here (e.g., charts, tables, or reports for chick/feed stock, sales, or farmer records).</p>
    </div>
    <div class="footer">
        <p>&copy; 2025 Young4ChickS. All rights reserved. | Contact: support@young4chicks.com</p>
    </div>
</bo

Sales Agent Dashboard Base Templatehtml

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Agent Dashboard - Young4ChickS</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; display: flex; }
        .sidebar { width: 250px; background-color: #f8f9fa; padding: 20px; height: 100vh; }
        .navbar-brand img { width: 150px; }
        .nav { list-style: none; padding: 0; }
        .nav-item { margin: 10px 0; }
        .nav-link { text-decoration: none; color: #333; font-size: 16px; display: flex; align-items: center; }
        .nav-link i { margin-right: 10px; }
        .logout-btn { background-color: #d32f2f; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; font-weight: 500; width: 100%; margin-top: 20px; cursor: pointer; transition: background-color 0.3s ease; }
        .content { flex-grow: 1; padding: 20px; }
        .footer { background-color: #333; color: #fff; text-align: center; padding: 10px; position: fixed; bottom: 0; width: 100%; }
    </style>
</head>
<body>
    <div class="sidebar">
        <a class="navbar-brand" href="#">
            <img src="{% static 'images/logo.png' %}" alt="Young4ChickS Logo">
        </a>
        <ul class="nav">
            <li class="nav-item"><a class="nav-link" href="/"><i class="fas fa-home"></i>Home</a></li>
            <li class="nav-item"><a class="nav-link" href="/salesagentdashboard/"><i class="fas fa-list"></i>Sales Agent Dash Board</a></li>
            <li class="nav-item"><a class="nav-link" href="/addrequest/"><i class="fas fa-plus"></i>Add Request</a></li>
            <li class="nav-item"><a class="nav-link" href="/registerfarmer/"><i class="fas fa-user-plus"></i>Register Farmer</a></li>
            <li class="nav-item"><a class="nav-link" href="/viewchickrequests/"><i class="fas fa-list"></i>View Chick Requests</a></li>
            <li class="nav-item"><a class="nav-link" href="/viewfeedrequests/"><i class="fas fa-seedling"></i>View Feed Requests</a></li>
        </ul>
        <button class="logout-btn" onclick="window.location.href='/logout/'">Logout</button>
    </div>
    <div class="content">
        <!-- Sales Agent Dashboard Content Placeholder -->
        <h1>Sales Agent Dashboard</h1>
        <p>Insert content here (e.g., forms for adding requests, tables for viewing chick/feed requests, or farmer registration details).</p>
    </div>
    <div class="footer">
        <p>&copy; 2025 Young4ChickS. All rights reserved. | Contact: support@young4chicks.com</p>
    </div>
</body>
</html>


