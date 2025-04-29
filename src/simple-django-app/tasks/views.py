from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Task
from .forms import TaskForm, SearchForm
from .documents import TaskDocument


class TaskListView(ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    ordering = ["-created_at"]


class TaskDetailView(DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    success_url = reverse_lazy("task-list")


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    success_url = reverse_lazy("task-list")


class TaskDeleteView(DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task-list")


def mark_as_completed(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.status = "completed"
    task.save()
    return redirect("task-list")


def search_tasks(request):
    query = request.GET.get("query", "")
    form = SearchForm(initial={"query": query})

    results = []
    if query:
        # Search in both title and description
        title_results = TaskDocument.objects.search(title=query)
        description_results = TaskDocument.objects.search(description=query)

        # Combine results (removing duplicates)
        result_ids = set()
        for task in list(title_results) + list(description_results):
            if task.id not in result_ids:
                results.append(task)
                result_ids.add(task.id)

    return render(request, "tasks/task_search_results.html", {"form": form, "query": query, "results": results})
