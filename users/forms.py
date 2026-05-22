from django import forms
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm

from .models import User, UserPreferences, Suggestion


class EmailForm(forms.Form):
    email_address = forms.EmailField(
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full pl-10',
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email',
            'autocapitalize': 'none',
        }),
        label='Email address',
        required=True,
    )


class PasswordResetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        label='New password',
        required=True,
        help_text='At least 8 characters. Cannot be entirely numeric or too common.',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        label='Confirm new password',
        required=True,
        help_text='Enter the same password again to confirm.',
    )


class NewPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        label='Current password',
        required=True,
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        label='New password',
        required=True,
        help_text='At least 8 characters. Cannot be entirely numeric or too common.',
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}),
        label='Confirm new password',
        required=True,
        help_text='Enter the same password again to confirm.',
    )


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email

    def create_user(self, commit=True):
        email = self.cleaned_data.get('email', None)
        user = User.objects.create_user(email=email)
        return user


class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ('confirm_cast_cancel',)
        widgets = {
            'confirm_cast_cancel': forms.CheckboxInput(),
        }


class SuggestionForm(forms.ModelForm):
    class Meta:
        model = Suggestion
        fields = ('category', 'title', 'body')
        widgets = {
            'category': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Short summary of your suggestion',
            }),
            'body': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 5,
                'placeholder': 'Describe your suggestion in detail...',
            }),
        }
