from django import forms
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm

from .models import User


class EmailForm(forms.Form):
    email_address = forms.EmailField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        label='Email address',
        required=True,
    )


class PasswordResetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Password',
        required=True,
        help_text='<ul><li>Your password can’t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can’t be a commonly used password.</li><li>Your password can’t be entirely numeric.</li></ul>',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm password',
        required=True,
        help_text='Enter the same password as before, for verification.'
    )


class NewPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Old password',
        required=True,
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='New password',
        required=True,
        help_text='<ul><li>Your password can’t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can’t be a commonly used password.</li><li>Your password can’t be entirely numeric.</li></ul>',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm password',
        required=True,
        help_text='Enter the same password as before, for verification.'
    )

class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def create_user(self, commit=True):
        email = self.cleaned_data.get('email', None)

        user = User.objects.create_user(email=email)
        return user

