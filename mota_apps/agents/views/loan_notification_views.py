# import logging
# from django.http import JsonResponse, HttpRequest
# from django.views import View
# from django.utils.translation import gettext_lazy as _
# from mota_apps.agents.tasks.loan_notification_task import run_loan_notification_task

# logger = logging.getLogger(__name__)

# class LoanNotificationView(View):
#     def post(self, request: HttpRequest, *args, **kwargs):
#         try:
#             fields = self._extract_notification_fields(request)
#             task = run_loan_notification_task.delay(test_user_emails=fields["test_user_emails"])
#             logger.info(f"Loan Notification Agent launched by user {request.user.id}, task ID: {task.id}")
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Loan Notification Agent launched successfully. You will receive an email with the results.'),
#                 'task_id': str(task.id)
#             }, status=200)
#         except Exception as e:
#             logger.error(f"Error launching Loan Notification Agent: {str(e)}", exc_info=True)
#             return JsonResponse({
#                 'success': False,
#                 'message': _('Failed to launch Loan Notification Agent. Please try again.')
#             }, status=500)

#     def _extract_notification_fields(self, request: HttpRequest) -> dict:
#         test_user_emails = request.POST.get("test_user_emails", "")
#         test_emails_list = [email.strip() for email in test_user_emails.split(",") if email.strip()] if test_user_emails else None
#         return {"test_user_emails": test_emails_list}