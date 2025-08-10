from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


@admin.register(UserProfile)
class CustomUserAdmin(UserAdmin):
	# Show extra fields in admin
	fieldsets = UserAdmin.fieldsets + (
		('Additional Info', {'fields': ('role', 'phone', 'title')}),
	)
	add_fieldsets = UserAdmin.add_fieldsets + (
		(None, {'fields': ('role', 'phone', 'title')}),
	)
	list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
	list_filter = ('role', 'is_staff', 'is_active')
	search_fields = ('username', 'email', 'phone')
