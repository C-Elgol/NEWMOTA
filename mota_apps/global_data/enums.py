from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

class LoanStatus(TextChoices):
    UNPAID = "UNPAID", _("Unpaid")
    PARTIAL = "PARTIAL", _("Partially Paid")
    PAID = "PAID", _("Fully Paid")