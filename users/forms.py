from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        initial='student'
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "role", "department", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"
        self.fields["email"].widget.attrs["placeholder"] = "Email address"
        self.fields["first_name"].widget.attrs["placeholder"] = "First name (optional)"
        self.fields["last_name"].widget.attrs["placeholder"] = "Last name (optional)"
        self.fields["department"].widget.attrs["placeholder"] = "Department (optional)"
        self.fields["department"].required = False
