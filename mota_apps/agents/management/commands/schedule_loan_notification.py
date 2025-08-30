import json
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

class Command(BaseCommand):
    help = 'Schedule the Loan Notification Agent task as a PeriodicTask.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            choices=['30-seconds', '3-days'],
            default='30-seconds',
            help='Schedule interval: "30-seconds" for testing, "3-days" for production.',
        )
        parser.add_argument(
            '--disable-other-tasks',
            action='store_true',
            help='Disable other loan notification tasks to avoid conflicts.',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        disable_other_tasks = options['disable_other_tasks']

        # Disable other loan notification tasks if requested
        if disable_other_tasks:
            PeriodicTask.objects.filter(
                task="mota_apps.agents.tasks.loan_notification_task.run_loan_notification_task"
            ).exclude(name=f"Run Loan Notification Every {interval.replace('-', ' ').title()}").update(enabled=False)
            self.stdout.write(self.style.SUCCESS('Disabled other loan notification tasks.'))

        # Create schedule and task
        if interval == '30-seconds':
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=30,
                period=IntervalSchedule.SECONDS,
            )
            task_name = "Run Loan Notification Every 30 Seconds"
            task_args = json.dumps([])  # Empty list, task will fetch emails from DB
        else:  # 3-days
            schedule, _ = CrontabSchedule.objects.get_or_create(
                hour=0, minute=0, day_of_month='*/3'
            )
            task_name = "Run Loan Notification Every 3 Days"
            task_args = json.dumps([])  # Empty list, task will fetch emails from DB

        task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                "task": "mota_apps.agents.tasks.loan_notification_task.run_loan_notification_task",
                "interval" if interval == '30-seconds' else "crontab": schedule,
                "args": task_args,
                "enabled": True,
            }
        )

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} PeriodicTask '{task_name}' (emails will be fetched from DB)"
        ))
