from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

_INPUT_ATTRS = {"class": "terminal-input", "dir": "ltr"}


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="نام_کاربری",
        widget=forms.TextInput(attrs={**_INPUT_ATTRS, "placeholder": "username"}),
    )
    password = forms.CharField(
        label="رمز_عبور",
        widget=forms.PasswordInput(attrs={**_INPUT_ATTRS, "placeholder": "••••••••"}),
    )


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "نام_کاربری"
        self.fields["username"].widget.attrs.update(
            {**_INPUT_ATTRS, "placeholder": "username"}
        )
        self.fields["email"].label = "ایمیل"
        self.fields["email"].required = True
        self.fields["email"].widget.attrs.update(
            {**_INPUT_ATTRS, "placeholder": "user@example.com"}
        )
        self.fields["password1"].label = "رمز_عبور"
        self.fields["password1"].widget.attrs.update(
            {**_INPUT_ATTRS, "placeholder": "••••••••"}
        )
        self.fields["password2"].label = "تکرار_رمز_عبور"
        self.fields["password2"].widget.attrs.update(
            {**_INPUT_ATTRS, "placeholder": "••••••••"}
        )
