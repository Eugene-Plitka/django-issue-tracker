from django import forms

from accounts.models import User

from .models import Comment, Issue, Label


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


class IssueManagementForm(forms.ModelForm):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
    )

    class Meta:
        model = Issue
        fields = (
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "labels",
        )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        if project is not None:
            self.fields["assignee"].queryset = User.objects.filter(
                project_memberships__project=project,
            ).distinct()

            self.fields["labels"].queryset = project.labels.all()


class IssueDeveloperForm(forms.ModelForm):
    assign_to_me = forms.BooleanField(
        required=False,
        label="Assign this issue to me",
    )

    class Meta:
        model = Issue
        fields = (
            "title",
            "description",
            "status",
            "labels",
        )

    def __init__(
        self,
        *args,
        project=None,
        user=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if project is not None:
            self.fields["labels"].queryset = project.labels.all()

        if user is not None and self.instance.reporter_id != user.id:
            self.fields.pop("title")
            self.fields.pop("description")


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ("name",)
