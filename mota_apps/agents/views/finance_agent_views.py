import logging
from decimal import Decimal
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
# from mota_apps.decorators.admin_required import admin_required
from mota_apps.users.models import User
from mota_apps.agents.tasks.finance_agent_task import run_finance_agent_task
from django.shortcuts import render
logger = logging.getLogger(__name__)

# @method_decorator(admin_required, name='dispatch')
class FinanceAgentView(View):
    def get(self, request):
        from mota_apps.finance.models import FinanceRecord
        from django.utils import timezone
        # Get all active members
        members = User.objects.filter(is_active=True, is_deleted=False)
        
        # Get current season from session or default to current month
        selected_season = request.session.get('selected_season')
        if selected_season:
            year = selected_season['year']
            month = selected_season['month']
            season = timezone.datetime(year, month, 1).strftime('%B %Y')
        else:
            season = timezone.now().strftime('%B %Y')

        return render(request, 'publics/dashboard/admin/pages/finance_agent/finance_agent.html', {
            'members': members,
            'season': season,
        })

    def post(self, request):
        try:
            agent_type = request.POST.get("agent_type")
            if agent_type != "finance":
                return JsonResponse({"success": False, "message": "Unknown agent_type."}, status=400)

            member_ids = request.POST.getlist("finance-members")
            entertainment = request.POST.get("finance-entertainment", '0.00')
            savings = request.POST.get("finance-savings", '0.00')
            njangi = request.POST.get("finance-njangi", '0.00')
            project = request.POST.get("finance-project", '0.00')
            others = request.POST.get("finance-others", '0.00')
            season_date = request.POST.get("finance-season")

            if not member_ids or not season_date:
                return JsonResponse({"success": False, "message": "Missing required fields: members or season."}, status=400)

            amounts = {
                "entertainment": str(Decimal(entertainment)),
                "savings": str(Decimal(savings)),
                "njangi": str(Decimal(njangi)),
                "project": str(Decimal(project)),
                "others": str(Decimal(others)),
            }

            user_email = request.user.email if request.user.is_authenticated else None
            task = run_finance_agent_task.delay(
                member_ids=[str(id) for id in member_ids],
                amounts=amounts,
                season_date=season_date,
                recorded_by_id=request.user.id,
                user_email=user_email,
            )

            logger.info(f"Finance Agent task launched by {request.user.email}, task_id={task.id}")
            return JsonResponse({
                "success": True,
                "message": "Finance agent started successfully. You will receive an email with the results.",
                "task_id": task.id,
            }, status=200)

        except Exception as e:
            logger.error(f"Error launching Finance Agent: {str(e)}", exc_info=True)
            return JsonResponse({"success": False, "message": f"Internal error: {str(e)}"}, status=500)