import os
import sys
import django

# Setup Django
sys.path.append(r"D:\Projects\VentaPOS\Desktop\sales")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales.settings')
django.setup()

from django.contrib.auth.models import User
from salesapp.models import Branch, Salesperson

try:
    # Ensure a branch exists
    branch, _ = Branch.objects.get_or_create(name='Main Cloud Branch')
    
    # Create the user
    user, created = User.objects.get_or_create(username='cloud_cashier')
    if created:
        user.set_password('password123')
        user.is_staff = True
        user.save()
        print("Cloud user created successfully.")
    else:
        print("Cloud user already exists.")
        
except Exception as e:
    print(f"Error: {e}")
