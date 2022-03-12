
from django.db import models
from datetime import datetime, timezone
from django.contrib.auth.models import User

from django.dispatch import receiver
from django.db.models.signals import post_save

STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)

class Task(models.Model):
    _old_status = None

    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    priority = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_status = self.status


class TaskHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    new_status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    time_of_change = models.DateTimeField(auto_now=True)

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null = True, blank = True)
    timing = models.IntegerField(default = 0)
    last_report = models.DateTimeField(null=True, default=datetime.now(timezone.utc).replace(hour=0))

@receiver(post_save, sender=User)
def addReport(instance, **kwargs):
    user = User.objects.get(pk=instance.id)
    report = Report.objects.filter(user=user)
    if report.count() <= 0:
        Report.objects.create(
            user=user,
            timing=0
        )