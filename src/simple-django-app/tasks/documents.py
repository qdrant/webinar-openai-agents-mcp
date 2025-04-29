from django_semantic_search import Document, VectorIndex
from django_semantic_search.decorators import register_document
from .models import Task


@register_document
class TaskDocument(Document):
    class Meta:
        model = Task
        indexes = [
            VectorIndex("title"),
            VectorIndex("description"),
        ]
