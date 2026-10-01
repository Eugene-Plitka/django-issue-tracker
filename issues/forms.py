from django import forms

from accounts.models import User

from .models import Issue


class IssueForm(forms.ModelForm):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
    )

    class Meta:
        model = Issue
        fields = (
            "title",
            "description",
            "priority",
            "assignee",
        )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        if project is not None:
            self.fields["assignee"].queryset = User.objects.filter(
                project_memberships__project=project,
            ).distinct()
