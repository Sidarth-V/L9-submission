from pytz import timezone
from celery.decorators import periodic_task
from datetime import datetime, timedelta, timezone
from django.core.mail import send_mail
from tasks.models import Report, Task

# Periodic Task
@periodic_task(run_every=timedelta(seconds=5))
def send():
    return_list = []
    to_send = Report.objects.filter(last_report__lte = (datetime.now(timezone.utc) - timedelta(days=1)))

    choices = [
    ["PENDING", "PENDING"],
    ["IN_PROGRESS", "IN_PROGRESS"],
    ["COMPLETED", "COMPLETED"],
    ["CANCELLED", "CANCELLED"],
    ]

    for item in to_send:
        tasks = Task.objects.filter(user=item.user, deleted = False).order_by('priority')

        email = f'Hello {item.user.username}. Please find your task report below:\n\n'

        for choice in choices:
            status_name = choice[0]
            status_id = choice[1]

            tasks_status_filter = tasks.filter(status = status_id)
            status_count = tasks_status_filter.count()

            choice.append(status_count)

            email += f'{status_name}: {status_count} tasks \n'
            for task in tasks_status_filter:
                email += f'Title: {task.title} \nPriority: ({task.priority}): \nDescription: {task.description} \nCreated on: {task.created_date}\n\n'


        send_mail("Tasks Mangager", email, "tasks@task_manger.org", [item.user.email])
        item.last_report = datetime.now(timezone.utc).replace(hour=item.timing)
        item.save()
        print(f"Completed Processing User {item.user.id}")
        return_list.append(f"Completed Processing User {item.user.username}")
    
    return return_list