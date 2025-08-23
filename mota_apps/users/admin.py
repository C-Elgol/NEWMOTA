from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, Partners, ContactUs, CompanySettings
from django.utils.translation import gettext_lazy as _


# Custom User admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        "email",
        "fullname",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "is_admin",
        "is_client",
        "is_visitor",
    )
    list_filter = ("is_staff", "is_active", "is_admin", "is_client", "is_visitor")
    search_fields = ("email", "first_name", "last_name", "fullname")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "fullname", "profile_picture")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_admin", "is_client", "is_visitor", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser")
        }),
    )

# Profile admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "country", "region", "city", "address")
    search_fields = ("user__email", "phone_number", "country", "region", "city")
    readonly_fields = ("user",)

# Partners admin
@admin.register(Partners)
class PartnersAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_filter = ("is_active",)

# ContactUs admin
@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "is_resolved", "created")
    search_fields = ("name", "email", "subject", "message")
    list_filter = ("is_read", "is_resolved", "created")
    readonly_fields = ("created",)  # ✅ remove 'updated'


# CompanySettings admin
@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "is_active", "primary_email", "phone_number")
    list_filter = ("is_active",)
    search_fields = ("company_name", "primary_email", "tax_id", "registration_number")
