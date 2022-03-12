from asyncio.base_tasks import _task_get_stack
from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_filters.rest_framework import (
    CharFilter,
    ChoiceFilter,
    DjangoFilterBackend,
    FilterSet,
    DateFromToRangeFilter,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ReadOnlyModelViewSet

from tasks.models import STATUS_CHOICES, Task, TaskHistory


class TaskSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "completed",
            "created_date",
            "deleted",
            "priority",
            "status",
            "user",
        ]
        read_only_fields = ("user", "created_date")


class TaskFilter(FilterSet):
    title = CharFilter(lookup_expr="icontains")
    status = ChoiceFilter(choices=STATUS_CHOICES)

    class Meta:
        model = Task
        fields = (
            "title",
            "status",
        )


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskHistorySerializer(ModelSerializer):
    class Meta:
        model = TaskHistory
        fields = ["id", "task", "old_status", "new_status", "time_of_change"]
        read_only_fields = ["task", "old_status", "new_status"]


class TaskHistoryFilter(FilterSet):
    time_of_change = DateFromToRangeFilter()
    old_status = ChoiceFilter(choices=STATUS_CHOICES)
    new_status = ChoiceFilter(choices=STATUS_CHOICES)

    class Meta:
        model = TaskHistory
        fields = ("task", "old_status", "new_status")


class TaskHistoryViewSet(ReadOnlyModelViewSet):
    queryset = TaskHistory.objects.all()
    serializer_class = TaskHistorySerializer
    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskHistoryFilter

    def get_queryset(self):
        return TaskHistory.objects.filter(user=self.request.user)


@receiver(pre_save, sender=Task)
def helper(sender, instance: Task, **kwargs):
    if Task.objects.filter(
        deleted=False, user=instance.user, priority=instance.priority, completed=False
    ).exists():
        old_tasks = (
            Task.objects.filter(
                deleted=False,
                user=instance.user,
                priority__gte=instance.priority,
                completed=False,
            )
            .exclude(pk=instance.id)
            .order_by("priority")
            .select_for_update()
        )

        changes = []
        flag = instance.priority
        for task in old_tasks:
            if flag != task.priority:
                break
            task.priority = task.priority + 1
            flag = flag + 1
            changes.append(task)

        with transaction.atomic():
            if changes:
                Task.objects.bulk_update(changes, ["priority"], batch_size=100)
        return


@receiver(pre_save, sender=Task)
def createNewHistory(sender, instance, **kwargs):
    if instance._old_status != instance.status:
        TaskHistory.objects.create(
            task=instance,
            old_status=instance._old_status,
            new_status=instance.status,
            user=instance.user
        )