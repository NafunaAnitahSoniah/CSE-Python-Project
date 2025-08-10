from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError

class UserProfile(AbstractUser): #abstract user is the model that helps us store a superadmin
    ROLE_CHOICES = (
        ('farmer', 'farmer'),
        ('sales_agent', 'sales_agent'),
        ('manager', 'manager'),
    )
    #the view related to this model should work in such a way that after choosing one's role, they are redirected to the respective dashboard
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='manager')
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(r'^\+?\d{10,15}$', 'Enter a valid phone number.')]
    )
    title = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = 'farmer_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

class ChickStock(models.Model):
    batch_name = models.CharField(max_length=25, unique=True)
    chick_type = models.CharField(max_length=15, choices=[('layer', 'Layer'), ('broiler', 'Broiler')])
    chick_breed = models.CharField(max_length=15, choices=[('local', 'Local'), ('exotic', 'Exotic')])
    chick_age = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    chick_price = models.PositiveIntegerField(default=1650)  # Fixed price per assignment
    stock_quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.batch_name} - {self.chick_type} - {self.chick_breed}"

    def clean(self):
        if self.stock_quantity < 0:
            raise ValidationError('Stock quantity cannot be negative.')

class FeedStock(models.Model):
    stock_name = models.CharField(max_length=25, unique=True)
    feed_name = models.CharField(max_length=25)
    feed_type = models.CharField(max_length=25)
    feed_brand = models.CharField(max_length=25)
    feed_quantity = models.PositiveIntegerField()
    expiry_date = models.DateField()
    purchase_price = models.PositiveIntegerField()
    selling_price = models.PositiveIntegerField()
    supplier = models.CharField(max_length=100)
    supplier_contact = models.CharField(max_length=15, unique=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.feed_name

    def clean(self):
        if self.expiry_date < timezone.now().date():
            raise ValidationError('Expiry date cannot be in the past.')

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    farmer_id = models.CharField(max_length=15, unique=True)
    farmer_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(validators=[MinValueValidator(20), MaxValueValidator(30)])
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    location = models.CharField(max_length=30)
    nin = models.CharField(
        max_length=14,
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9]{14}$', 'NIN must be 14 alphanumeric characters.')]
    )
    phone_number = models.CharField(max_length=15)
    recommender_name = models.CharField(max_length=50)
    recommender_nin = models.CharField(max_length=14)
    recommender_tel = models.CharField(max_length=15)
    registered_by = models.CharField(max_length=50)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.farmer_id

    def clean(self):
        # Ensure age matches date_of_birth
        today = timezone.now().date()
        calculated_age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        if calculated_age != self.age:
            raise ValidationError('Age does not match date of birth.')

class ChickRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    farmer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    chick_request_id = models.CharField(max_length=15, unique=True)
    farmer_type = models.CharField(max_length=10, choices=[('starter', 'Starter'), ('returning', 'Returning')])
    chick_type = models.CharField(max_length=15, choices=[('layer', 'Layer'), ('broiler', 'Broiler')])
    chick_breed = models.CharField(max_length=15, choices=[('local', 'Local'), ('exotic', 'Exotic')])
    quantity = models.PositiveIntegerField()
    chick_period = models.PositiveIntegerField()  # Age of chicks requested
    feed_taken = models.BooleanField(default=True)  # Whether feed is taken
    payment_terms = models.CharField(
        max_length=20,
        choices=[('mobile_money', 'Mobile Money'), ('visa', 'Visa'), ('cash', 'Cash')]
    )
    request_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_requests')
    received_through = models.CharField(max_length=10, choices=[('walk-in', 'Walk-in'), ('phonecall', 'Phonecall')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_on = models.DateTimeField(null=True, blank=True)
    delivered = models.BooleanField(default=False)

    def __str__(self):
        return self.chick_request_id

    def clean(self):
        # Validate quantity based on farmer type
        if self.farmer_type == 'starter' and self.quantity != 100:
            raise ValidationError('Starter farmers must request exactly 100 chicks.')
        if self.farmer_type == 'returning' and self.quantity > 500:
            raise ValidationError('Returning farmers cannot request more than 500 chicks.')
        # Check stock availability
        stock = ChickStock.objects.filter(chick_type=self.chick_type, chick_breed=self.chick_breed).first()
        if stock and stock.stock_quantity < self.quantity:
            raise ValidationError('Requested quantity exceeds available stock.')
        # Check 4-month frequency
        last_request = ChickRequest.objects.filter(farmer=self.farmer, request_date__gte=timezone.now() - timedelta(days=120)).exclude(id=self.id).first()
        if last_request:
            raise ValidationError('You can only submit a request every 4 months.')

class FeedAllocation(models.Model):
    feed_request_id = models.CharField(max_length=15, unique=True)
    feed_name = models.CharField(max_length=25)
    feed_type = models.CharField(max_length=25)
    feed_brand = models.CharField(max_length=25)
    chick_request = models.ForeignKey(ChickRequest, on_delete=models.CASCADE)
    bags_allocated = models.PositiveIntegerField(default=2)
    amount_due = models.PositiveIntegerField()
    payment_due_date = models.DateField()
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid')],
        default='pending'
    )

    def __str__(self):
        return self.feed_request_id

    def save(self, *args, **kwargs):
        # Auto-set payment_due_date to 2 months from now
        if not self.payment_due_date:
            self.payment_due_date = timezone.now().date() + timedelta(days=60)
        super().save(*args, **kwargs)

class Sale(models.Model):
    sale_id = models.CharField(max_length=15, unique=True)
    chick_request = models.OneToOneField(ChickRequest, on_delete=models.CASCADE)
    total_amount = models.PositiveIntegerField()  # quantity * chick_price
    created_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.sale_id




