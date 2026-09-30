from django import forms

from accounts.models import User
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "key", "description")


class ProjectMemberForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none())

    def __init__(self, *args, workspace=None, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        if workspace is not None:
            queryset = User.objects.filter(workspace_memberships__workspace=workspace)

            if project is not None:
                queryset = queryset.exclude(project_memberships__project=project)

            self.fields["user"].queryset = queryset.distinct()
