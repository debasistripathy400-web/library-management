import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth.models import User
from library.models import Book, Category, Member, Transaction

def seed_db():
    # 1. Create Superuser User
    if not User.objects.filter(username='admin').exists():
        print("Creating admin user...")
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    # 2. Create Categories
    categories_data = [
        {'name': 'Fiction', 'description': 'Novels and fantasy stories.'},
        {'name': 'Science', 'description': 'Physics, Chemistry, Biology.'},
        {'name': 'Technology', 'description': 'Computer science, programming, and software engineering.'},
        {'name': 'History', 'description': 'World history, biographies.'},
    ]
    categories = {}
    for cat_data in categories_data:
        cat, created = Category.objects.get_or_create(name=cat_data['name'], defaults={'description': cat_data['description']})
        categories[cat.name] = cat
        
    # 3. Create Books
    books_data = [
        {'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'category': categories['Fiction'], 'isbn': '9780743273565', 'quantity': 3, 'available': 3, 'desc': 'A story of the Jazz Age.'},
        {'title': 'Clean Code', 'author': 'Robert C. Martin', 'category': categories['Technology'], 'isbn': '9780132350884', 'quantity': 5, 'available': 5, 'desc': 'A Handbook of Agile Software Craftsmanship.'},
        {'title': 'A Brief History of Time', 'author': 'Stephen Hawking', 'category': categories['Science'], 'isbn': '9780553380163', 'quantity': 2, 'available': 2, 'desc': 'From the Big Bang to Black Holes.'},
        {'title': 'Design Patterns', 'author': 'Erich Gamma et al.', 'category': categories['Technology'], 'isbn': '9780201633610', 'quantity': 4, 'available': 4, 'desc': 'Elements of Reusable Object-Oriented Software.'},
        {'title': '1984', 'author': 'George Orwell', 'category': categories['Fiction'], 'isbn': '9780451524935', 'quantity': 6, 'available': 6, 'desc': 'Dystopian social science fiction novel and cautionary tale.'},
    ]
    for book_data in books_data:
        Book.objects.get_or_create(
            title=book_data['title'],
            defaults={
                'author': book_data['author'],
                'category': book_data['category'],
                'isbn': book_data['isbn'],
                'quantity': book_data['quantity'],
                'available': book_data['available'],
                'description': book_data['desc']
            }
        )

    # 4. Create Members
    members_data = [
        {'name': 'John Doe', 'email': 'john@example.com', 'phone': '9876543210', 'gender': 'M'},
        {'name': 'Jane Smith', 'email': 'jane@example.com', 'phone': '8765432109', 'gender': 'F'},
        {'name': 'Alice Johnson', 'email': 'alice@example.com', 'phone': '7654321098', 'gender': 'F'},
    ]
    for member_data in members_data:
        Member.objects.get_or_create(
            email=member_data['email'],
            defaults={
                'name': member_data['name'],
                'phone': member_data['phone'],
                'gender': member_data['gender'],
                'address': '123 Main St, City'
            }
        )
        
    print("Database seeded successfully with Categories, Books, and Members.")

if __name__ == '__main__':
    seed_db()
