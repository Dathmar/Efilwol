import requests
from django.conf import settings
from django.urls import reverse
import json

def send_password_reset(user, token):
    api_key = settings.MAILGUN_API_KEY
    data = {
        "url": f'{settings.BASE_URL}{reverse('users:reset-password', args=[user.pk, token])}'
    }
    response = requests.post(
		"https://api.mailgun.net/v3/mg.efilwol.com/messages",
		auth=("api", f"{api_key}"),
		data={"from": "Mailgun Sandbox <postmaster@mg.efilwol.com>",
			"to": "Asher Danner <asher.danner@gmail.com>",
			"subject": "Your Password Reset Request",
			"template": "password reset",
			"h:X-Mailgun-Variables": f"{json.dumps(data)}"})
    print(response.text)
