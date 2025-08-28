from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from mota_apps.finance.models import FinanceRecord
from mota_apps.users.models import User

class FinanceAgent:
    """
    Agent for batch-filling finance records for multiple members.
    """

    def __init__(self, member_ids: list[str], amounts: dict, season_date: str, recorded_by_id: str):
        self.member_ids = member_ids
        self.amounts = amounts
        self.season_date = season_date
        try:
            self.season_date = datetime.strptime(season_date, "%B %Y").replace(day=1).date()
        except ValueError:
            raise ValueError(f"Invalid season_date format: {season_date}. Expected format like 'January 2025'.")
        self.recorded_by = User.objects.get(id=recorded_by_id)

    def run_agent(self) -> dict:
        processed_members = []
        for member_id in self.member_ids:
            member = User.objects.get(id=member_id)
            record, created = FinanceRecord.objects.get_or_create(
                member=member,
                season_date=self.season_date,
                defaults={
                    'recorded_by': self.recorded_by,
                    'net_income': Decimal('0.00'),  # Default; adjust if needed
                    'created': timezone.now(),
                }
            )
            record.entertainment_fees = Decimal(self.amounts['entertainment'])
            record.savings = Decimal(self.amounts['savings'])
            record.njangi = Decimal(self.amounts['njangi'])
            record.project = Decimal(self.amounts['project'])
            record.others = Decimal(self.amounts['others'])
            record.updated_at = timezone.now()
            record.save()
            processed_members.append(member.get_full_name)

        return {
            "processed_members": processed_members,
            "season_date": self.season_date,
        }