import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

user = User.objects.get(username='admin')
client = Client()
client.force_login(user)

try:
    response = client.get('/admin/')
    if response.status_code != 200:
        print(f"Status Code: {response.status_code}")
        print(response.content.decode('utf-8'))
    else:
        print("Success! /admin/ is accessible.")
except Exception as e:
    import traceback
    traceback.print_exc()
