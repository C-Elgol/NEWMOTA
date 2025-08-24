import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel, ActivatorModel
from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager


class MotaBaseModel(TimeStampedModel, ActivatorModel):
    """
    Name: MotaBaseModel
    Description: Abstract base model providing a UUID primary key, soft deletion, and metadata for all models.
    Author: ayemeleelgol@gmail.com
    """
    id = models.UUIDField(
        default=uuid.uuid4,
        null=False,
        blank=False,
        unique=True,
        primary_key=True,
        editable=False
    )
    is_deleted = models.BooleanField(default=False, help_text=_("Marks the record as deleted without removing it."))
    metadata = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text=_("Stores additional metadata in JSON format.")
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address associated with the record creation or update.")
    )
    class Meta:
        abstract = True


class User(MotaBaseModel, PermissionsMixin, AbstractBaseUser):
    """
    Name: User
    Description: Custom user model with email as the unique identifier and role-based flags.
    Author: ayemeleelgol@gmail.com
    """
    email = models.EmailField(
        _("email address"),
        blank=False,
        null=False,
        unique=True,
        error_messages={"unique": _("A user with that email already exists.")}
    )
    fullname = models.CharField(max_length=100, null=True, blank=True, help_text=_("Full name of the user."))
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into the admin site.")
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Designates whether this user should be treated as active. Unselect instead of deleting accounts.")
    )
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_("Designates that this user has all permissions without explicitly assigning them.")
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text=_("User's IP address."))

    # Role-based fields
    is_visitor = models.BooleanField(
        _("is visitor"),
        default=False,
        help_text="Designates for only views the data but can't edit that is all input are disable in the admin site",
    )
    is_client = models.BooleanField(
        _("is client"), 
        default=False, 
        help_text=_("User is a client.")
    )
    is_admin = models.BooleanField(
        _("is admin"), 
        default=False, 
        help_text=_("User is an admin.")
    )
    is_manually_deleted = models.BooleanField(
        _("is manually deleted"),
        default=False,
        help_text=_("Marks if the user was manually deleted.")
    )

    # New field for terms acceptance
    has_accepted_terms = models.BooleanField(
        _("has accepted terms"),
        default=False,
        help_text=_("Indicates whether the user has accepted the Terms of Service and Privacy Policy during registration.")
    )

    # New field for profile picture
    profile_picture = models.ImageField(
        verbose_name=_("Profile Picture"),
        null=True,
        blank=True,
        upload_to="profile/",
        help_text=_("User's profile picture.")
    )


    # Authentication settings
    username = None
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def has_perm(self, perm, obj=None):
        """Check if the user has a specific permission."""
        return True  # Simplified for superusers; adjust based on your needs

    def clean(self):
        """Normalize email before saving."""
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    @property
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.fullname

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split("@")[0]

    def __str__(self):
        return self.email

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return None


class Profile(MotaBaseModel):
    """
    Name: Profile
    Description: Stores user profile information for physical product delivery.
    Author: ayemeleelgol@gmail.com
    """
    user = models.OneToOneField(
        'User',
        on_delete=models.PROTECT,
        related_name='profile',
        help_text=_("Associated user account.")
    )
    country = models.CharField(_("Country"), max_length=50, blank=True)
    phone_number = models.CharField(_("Phone Number"), max_length=255, blank=True)
    region = models.CharField(_("Region"), max_length=50, default="Cameroon", blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    address = models.CharField(_("Address"), max_length=100, blank=True)
    zip_code = models.CharField(_("Zip Code"), max_length=20, default="00000", blank=True)

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        return f"{self.user.email}'s Profile"


def partner_logo_path(instance, filename):
    """Generate file path for partner logos."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'partners/logos/{filename}'


class Partners(MotaBaseModel):
    """
    class: Partners
    Description: Stores information about business partners or collaborators.
    Author: ayemeleelgol@gmail.com
    """
    name = models.CharField(
        _("Name"),
        max_length=255,
        unique=True,
        help_text=_("Name of the partner organization.")
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text=_("URL-friendly identifier for the partner.")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description of the partner organization.")
    )
    logo = models.ImageField(
        _("Logo"),
        upload_to=partner_logo_path,
        max_length=1000,
        null=True,
        blank=True,
        help_text=_("Partner's logo image.")
    )
    website = models.URLField(
        _("Website"),
        blank=True,
        null=True,
        help_text=_("Partner's website URL.")
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Indicates whether the partner is actively displayed.")
    )

    class Meta:
        verbose_name = _('Partner')
        verbose_name_plural = _('Partners')
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_deleted']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ... [autres imports et classes inchangées] ...

class ContactUs(MotaBaseModel):
    """
    Stocke les soumissions de formulaires de contact ou les demandes.
    Auteur : ayemeleelgol@gmail.com
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_requests',
        help_text=_("Utilisateur ayant soumis le formulaire, s'il est authentifié.")
    )
    name = models.CharField(
        _("Nom"),
        max_length=255,
        help_text=_("Nom de la personne soumettant le formulaire.")
    )
    email = models.EmailField(
        _("Email"),
        help_text=_("Adresse email de contact.")
    )
    subject = models.CharField(
        _("Sujet"),
        max_length=255,
        help_text=_("Sujet de la demande.")
    )
    message = models.TextField(
        _("Message"),
        help_text=_("Contenu de la demande.")
    )
    is_resolved = models.BooleanField(
        _("Est Résolu"),
        default=False,
        help_text=_("Champ conservé pour compatibilité avec l'admin, non utilisé dans le dashboard.")
    )
    is_read = models.BooleanField(  # Nouveau champ pour "lu"
        _("Est Lu"),
        default=False,
        help_text=_("Indique si le message a été ouvert/lu par un admin.")
    )

    class Meta:
        verbose_name = _('Contactez-nous')
        verbose_name_plural = _('Entrées Contactez-nous')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['created']),
        ]
        ordering = ['-created']

    def __str__(self):
        return f"{self.subject} - {self.email}"


class CompanySettings(MotaBaseModel):
    """
    Company-wide configuration settings
    """
    # Basic Information
    company_name = models.CharField(
        max_length=255,
        default="Soprescom",
        help_text=_("The official name of the company")
    )
    company_logo = models.ImageField(
        upload_to='company/logo/',
        null=True,
        blank=True,
        help_text=_("Main company logo (preferably in SVG or PNG format)")
    )
    favicon = models.ImageField(
        upload_to='company/favicon/',
        null=True,
        blank=True,
        help_text=_("Favicon for the website")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Mark this configuration as active")
    )

    # Contact Information
    primary_email = models.EmailField(
        default="contact@soprescom.com",
        help_text=_("Primary contact email address")
    )
    support_email = models.EmailField(
        blank=True,
        null=True,
        help_text=_("Customer support email address")
    )
    sales_email = models.EmailField(
        blank=True,
        null=True,
        help_text=_("Sales inquiries email address")
    )
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        help_text=_("Primary contact phone number")
    )
    secondary_phone = PhoneNumberField(
        blank=True,
        null=True,
        help_text=_("Secondary contact phone number")
    )

    # Address Information
    physical_address = models.TextField(
        blank=True,
        null=True,
        help_text=_("Physical company address")
    )
    postal_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Postal address if different from physical address")
    )

    # Social Media
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)

    # Business Information
    tax_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Company tax identification number")
    )
    registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Company registration number")
    )
    vat_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text=_("VAT percentage applied to products/services")
    )

    # Operational Settings
    working_hours = models.CharField(
        max_length=255,
        default="Monday-Friday, 9:00 AM - 5:00 PM",
        help_text=_("Company working hours")
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        help_text=_("Company timezone")
    )

    # Legal Content
    terms_of_service = models.TextField(
        blank=True,
        null=True,
        help_text=_("Terms of service content")
    )
    privacy_policy = models.TextField(
        blank=True,
        null=True,
        help_text=_("Privacy policy content")
    )
    refund_policy = models.TextField(
        blank=True,
        null=True,
        help_text=_("Refund policy content")
    )

    # SEO Settings
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        help_text=_("Default meta title for SEO")
    )
    meta_description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Default meta description for SEO")
    )
    meta_keywords = models.TextField(
        blank=True,
        null=True,
        help_text=_("Default meta keywords for SEO")
    )

    class Meta:
        verbose_name = _("Company Configuration")
        verbose_name_plural = _("Company Configurations")
        ordering = ['-is_active', 'company_name']

    def __str__(self):
        return f"{self.company_name} ({'Active' if self.is_active else 'Inactive'})"

    @classmethod
    def get_active(cls):
        """Get the active configuration"""
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def get_solo(cls):
        """Singleton pattern fallback"""
        return cls.objects.first() or cls.objects.create()
