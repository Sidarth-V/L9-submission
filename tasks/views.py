from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tasks.forms import TaskCreateForm, ReportForm
from tasks.models import Task, Report
from django.db import transaction

class AuthorisedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)

class GenericTaskView(AuthorisedTaskManager, ListView):
    queryset = Task.objects.filter(deleted=False)
    template_name = "tasks.html"
    context_object_name = "tasks"
    paginate_by = 3

    def get_queryset(self):
        search_term = self.request.GET.get("search")
        current_tasks = Task.objects.filter(
            deleted=False, user=self.request.user
        ).order_by("completed", "priority")
        if search_term:
            current_tasks = current_tasks.filter(title__icontains=search_term)
        return current_tasks
    
    def get_context_data(self, **kwargs):          
        context = super().get_context_data(**kwargs)                     
        completed = Task.objects.filter(
            deleted=False, user=self.request.user, completed=True
        ).count
        context["completed"] = completed
        return context

class GenericCompletedTaskView(LoginRequiredMixin, ListView):
    queryset = Task.objects.filter(deleted=False)
    template_name = "completed_tasks.html"
    context_object_name = "tasks"
    paginate_by = 3

    def get_queryset(self):
        current_tasks = Task.objects.filter(
            deleted=False, completed=True, user=self.request.user
        )
        return current_tasks

class GenericTaskCreateView(LoginRequiredMixin, CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"

    def form_valid(self, form):
        self.object = form.save()
        self.object.user = self.request.user
        helper(self.request.user, int(form.cleaned_data.get("priority")), form)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericPendingTaskView(LoginRequiredMixin, ListView):
    queryset = Task.objects.filter(deleted=False)
    template_name = "pending_tasks.html"
    context_object_name = "tasks"
    paginate_by = 3

    def get_queryset(self):
        search_term = self.request.GET.get("search")
        current_tasks = Task.objects.filter(
            deleted=False, completed=False, user=self.request.user
        ).order_by("priority")
        if search_term:
            current_tasks = current_tasks.filter(title__icontains=search_term)
        return current_tasks


class GenericTaskDetailView(AuthorisedTaskManager, DetailView):
    model = Task
    template_name = "task_detail.html"


class GenericTaskUpdateView(AuthorisedTaskManager, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_update.html"
    success_url = "/tasks"

    def form_valid(self, form):
        self.object = form.save()
        self.object.user = self.request.user
        helper(self.request.user, int(form.cleaned_data.get("priority")), form)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskDeleteView(AuthorisedTaskManager, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = "/tasks"


class GenericTaskCompleteView(AuthorisedTaskManager, UpdateView):
    model = Task
    fields = ["completed"]
    template_name = "task_complete.html"
    success_url = "/tasks"

class GenericReportView(UpdateView):
    form_class = ReportForm
    template_name = "report.html"
    success_url = "/tasks"

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)

def helper(user, priority, form):
    if Task.objects.filter(
        deleted=False, user=user, priority=priority, completed=False
    ).exists():
        old_tasks = (
            Task.objects.filter(
                deleted=False,
                user=user,
                priority__gte=priority,
                completed=False,
            )
            .exclude(pk=form.instance.id)
            .order_by("priority")
            .select_for_update()
        )

        changes = []
        flag = priority
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