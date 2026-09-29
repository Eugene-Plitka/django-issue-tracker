from django import forms

from .models import Workspace, WorkspaceMembership


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ("name", "slug")


class WorkspaceMemberForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=WorkspaceMembership.Role.choices,
    )
