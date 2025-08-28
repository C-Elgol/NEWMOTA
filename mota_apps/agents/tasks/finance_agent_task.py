import logging
from celery import shared_task
from mota_apps.agents.models.finance_agent import FinanceAgent
from mota_apps.agents.tasks.email_tasks import send_agent_task_email

logger = logging.getLogger(__name__)

@shared_task
def run_finance_agent_task(member_ids: list[str], amounts: dict, season_date: str, recorded_by_id: str, user_email: str = None) -> str:
    try:
        logger.info(f"Starting Finance Agent task for user_email={user_email}, season_date={season_date}")
        finance_agent = FinanceAgent(
            member_ids=member_ids,
            amounts=amounts,
            season_date=season_date,
            recorded_by_id=recorded_by_id,
        )
        result = finance_agent.run_agent()

        logger.info(f"Finance Agent task completed successfully for {len(result['processed_members'])} members")

        # Send success email
        if user_email:
            send_agent_task_email.delay(
                user_email=user_email,
                task_type="finance",
                status="success",
                details={
                    "processed_members": ", ".join(result["processed_members"]),
                    "season_date": season_date,
                },
            )
        return f"Processed {len(result['processed_members'])} members"

    except Exception as e:
        logger.error(f"Finance Agent task failed: {str(e)}", exc_info=True)
        if user_email:
            send_agent_task_email.delay(
                user_email=user_email,
                task_type="finance",
                status="failure",
                details={"error": str(e)},
            )
        raise