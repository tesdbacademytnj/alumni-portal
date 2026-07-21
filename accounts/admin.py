from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AdminProfile

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'username', 'is_admin_user', 'is_staff')
    list_filter = ('is_admin_user', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'mobile', 'city', 'batch', 'institute')}),
        ('Admin Login', {'fields': ('username',), 'description': 'Only used by admin accounts to log in at /accounts/admin-login/.'}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin_user')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2', 'full_name')}),
    )
    search_fields = ('email', 'full_name', 'username')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AdminProfile)
