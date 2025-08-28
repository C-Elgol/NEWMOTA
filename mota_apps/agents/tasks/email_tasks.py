from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from mota_apps.agents.utils.email_utils import send_email_with_logo

@shared_task
def send_agent_task_email(user_email: str, task_type: str, status: str, details: dict):
    subject = f"Finance Agent Task - {status.capitalize()}"

    # Render HTML content
    context = {
        "site_name": settings.SITE_NAME,
        "processed_members": details.get("processed_members", "N/A"),
        "season_date": details.get("season_date", "N/A"),
        "error": details.get("error", "Unknown error"),
        "status": status,
    }
    html_content = render_to_string("publics/emails/finance_agent_notification.html", context)
    plain_text = strip_tags(html_content)

    try:
        send_email_with_logo(
            subject=subject,
            plain_text=plain_text,
            html_content=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")