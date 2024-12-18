from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required

from .forms import EmailForm, PasswordResetForm, NewPasswordChangeForm, UserCreationForm
from .models import User

import logging

logger = logging.getLogger('console_only')


def send_password_reset(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email_address']
            try:
                user = User.objects.get(email__iexact=email)
                user.send_password_reset_email()
            except Exception as e:
                logger.error(e)

            return redirect(reverse('users:password-reset-done'))
    else:
        form = EmailForm()

    return render(request, 'users/password_management/password_reset_form.html', {'form': form})


def password_reset_done(request):
    return render(request, 'users/password_management/password_reset_done.html')


def reset_password(request, pk, password_reset_token):
    user = User.objects.get(pk=pk)
    if request.method == 'POST':
        form = PasswordResetForm(user, request.POST)
        if form.is_valid():
            password = form.cleaned_data['new_password1']
            user.set_password(password)
            user.save()
            return redirect(reverse('users:password-reset-complete'))
    else:
        form = PasswordResetForm(user)

    valid_link = user.validate_password_reset_token(password_reset_token)

    context = {
        'valid_link': valid_link,
        'form': form
    }
    return render(request, 'users/password_management/password_reset_confirm.html', context)


@login_required()
def change_password(request):
    if request.method == 'POST':
        form = NewPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            if not request.user.check_password(old_password):
                form.add_error('old_password', 'Old password is incorrect')
                return render(request, 'users/password_management/password_change_form.html', {'form': form})

            password = form.cleaned_data['new_password1']
            request.user.set_password(password)
            request.user.save()
            return redirect(reverse('users:password-reset-complete'))
    else:
        form = NewPasswordChangeForm(request.user)

    context = {
        'form': form
    }
    return render(request, 'users/password_management/password_change_form.html', context)


def password_reset_complete(request):
    return render(request, 'users/password_management/password_reset_complete.html')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.create_user()
            return redirect('users:signup-complete')
        else:
            logger.error(form.errors)
    else:
        form = UserCreationForm()

    return render(request, 'users/signup.html', {'form': form})


def signup_complete(request):
    return render(request, 'users/signup_complete.html')

def give_me_script(request):
    if request.user.is_authenticated:
        user = request.user
        logger.info(f"User {user.email} is giving me a script")
        user.add_random_script()

    return redirect(reverse('game:index'))