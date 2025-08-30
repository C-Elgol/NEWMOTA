from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from mota_apps.agents.utils.email_utils import send_email_with_logo
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_agent_task_email(user_email: str, task_type: str, status: str, details: dict):
    logger.info(f"Sending email for task_type={task_type}, user_email={user_email}, status={status}")
    subject = f"{task_type.replace('_', ' ').title()} - {status.capitalize()}"
    context = {
        "site_name": settings.SITE_NAME,
        "processed_members": details.get("processed_members", "N/A"),
        "season_date": details.get("season_date", "N/A"),
        "error": details.get("error", "Unknown error"),
        "status": status,
        "message": details.get("message", ""),
        "loans": details.get("loans", []),
    }
    template_name = f"publics/emails/{task_type}.html"
    logger.debug(f"Rendering template: {template_name}")
    try:
        html_content = render_to_string(template_name, context)
        plain_text = strip_tags(html_content)
        logger.debug(f"Rendered HTML content: {html_content[:200]}...")
    except Exception as e:
        logger.error(f"Failed to render template {template_name}: {str(e)}")
        raise

    try:
        send_email_with_logo(
            subject=subject,
            plain_text=plain_text,
            html_content=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        logger.info(f"Email sent successfully to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")