from django.contrib import admin
from .models import (
    FinanceRecord, Loan, LoanPayment, Njangi,
    Interest, ProjectRecord, Expenditure
)

# ---------------------------
# FinanceRecord Admin
# ---------------------------
@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = ('member', 'season_date', 'net_income', 'entertainment_fees', 'savings', 'njangi', 'project', 'others', 'recorded_by')
    list_filter = ('season_date',)
    search_fields = ('member__email', 'member__fullname', 'recorded_by__email')
    readonly_fields = ('id',)

# ---------------------------
# Loan Admin
# ---------------------------
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('member', 'season_date', 'amount_borrowed', 'amount_paid', 'interest_to_be_paid', 'status', 'borrow_date')
    list_filter = ('status', 'season_date')
    search_fields = ('member__email', 'member__fullname', 'id_card_number')
    readonly_fields = ('id',)

# ---------------------------
# LoanPayment Admin
# ---------------------------
@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'season_date', 'amount', 'payment_date', 'recorded_by')
    list_filter = ('season_date', 'payment_date')
    search_fields = ('loan__member__email', 'loan__member__fullname')
    readonly_fields = ('id',)

# ---------------------------
# Njangi Admin
# ---------------------------
@admin.register(Njangi)
class NjangiAdmin(admin.ModelAdmin):
    list_display = ('user', 'season_date', 'transaction_id', 'member_id_number', 'position', 'amount', 'benefited_date')
    list_filter = ('season_date',)
    search_fields = ('user__email', 'user__fullname', 'transaction_id', 'member_id_number')
    readonly_fields = ('id',)

# ---------------------------
# Interest Admin
# ---------------------------
@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('member', 'season_date', 'total_savings', 'interest_share')
    list_filter = ('season_date',)
    search_fields = ('member__email', 'member__fullname')
    readonly_fields = ('id',)

# ---------------------------
# ProjectRecord Admin
# ---------------------------
@admin.register(ProjectRecord)
class ProjectRecordAdmin(admin.ModelAdmin):
    list_display = ('season_date', 'amount_collected', 'interest_collected', 'date_collected', 'recorded_by')
    list_filter = ('season_date', 'date_collected')
    search_fields = ('recorded_by__email', 'recorded_by__fullname')
    readonly_fields = ('id',)

# ---------------------------
# Expenditure Admin
# ---------------------------
@admin.register(Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = ('season_date', 'entertainment_spent', 'other_expenditures', 'recorded_by')
    list_filter = ('season_date',)
    search_fields = ('recorded_by__email', 'recorded_by__fullname')
    readonly_fields = ('id',)
