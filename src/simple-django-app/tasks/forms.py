from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status", "due_date"]
        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search tasks...",
            }
        ),
    )
