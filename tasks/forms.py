from django.forms import ModelForm
from django.contrib.auth.mixins import LoginRequiredMixin
from tasks.models import Task
from tasks.models import Report

class TaskCreateForm(LoginRequiredMixin, ModelForm):
    def clean_title(self):
        title = self.cleaned_data["title"]
        return title

    class Meta:
        model = Task
        fields = ["title", "description", "priority", "completed"]

class ReportForm(ModelForm):

    class Meta:
        model = Report
        fields = ["timing"]