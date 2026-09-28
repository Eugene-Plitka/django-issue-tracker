from django.db import models

from workspaces.models import Workspace


class Project(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=150)
    key = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                name="unique_project_key_per_workspace",
            )
        ]

    def __str__(self):
        return f"{self.key} - {self.name}"
