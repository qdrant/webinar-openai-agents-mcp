from django.urls import path
from . import views

urlpatterns = [
    path("", views.TaskListView.as_view(), name="task-list"),
    path("task/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("task/new/", views.TaskCreateView.as_view(), name="task-create"),
    path("task/<int:pk>/update/", views.TaskUpdateView.as_view(), name="task-update"),
    path("task/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task-delete"),
    path("task/<int:pk>/complete/", views.mark_as_completed, name="task-complete"),
    path("search/", views.search_tasks, name="task-search"),
]
