"""
Forms for the Library Management System.
Handles validation for books, members, and transactions.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Book, Member, Transaction, Category
from django.utils import timezone
from datetime import timedelta


class LoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )


class CategoryForm(forms.ModelForm):
    """Form for adding/editing book categories."""
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }


class BookForm(forms.ModelForm):
    """Form for adding and editing books."""
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'category', 'publisher', 'publication_year',
                  'description', 'quantity', 'available', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author name'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN (optional)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Publisher'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Book description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'available': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get('quantity')
        avail = cleaned_data.get('available')
        if qty is not None and avail is not None:
            if avail > qty:
                raise forms.ValidationError("Available copies cannot exceed total quantity.")
        return cleaned_data


class BookSearchForm(forms.Form):
    """Search form for books."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, author, or category...',
            'id': 'bookSearchInput',
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class MemberForm(forms.ModelForm):
    """Form for registering and editing members."""
    class Meta:
        model = Member
        fields = ['name', 'email', 'phone', 'address', 'gender', 'is_active', 'photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) < 10 or len(phone) > 15:
            raise forms.ValidationError("Phone number must be 10-15 digits.")
        return phone


class MemberUserForm(forms.ModelForm):
    """Form to create a login account for a member."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=6,
        help_text="Minimum 6 characters."
    )

    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login username'}),
        }


class IssueBookForm(forms.ModelForm):
    """Form to issue a book to a member."""
    class Meta:
        model = Transaction
        fields = ['book', 'member', 'due_date', 'fine_per_day', 'remarks']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-select'}),
            'member': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fine_per_day': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any remarks'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available books
        self.fields['book'].queryset = Book.objects.filter(available__gt=0)
        # Only show active members
        self.fields['member'].queryset = Member.objects.filter(is_active=True)
        # Default due date: 14 days from today
        if not self.instance.pk:
            self.initial['due_date'] = (timezone.now().date() + timedelta(days=14)).strftime('%Y-%m-%d')

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date <= timezone.now().date():
            raise forms.ValidationError("Due date must be in the future.")
        return due_date



class ReturnBookForm(forms.Form):
    """Form to mark a book as returned."""
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Return remarks'})
    )
    waive_fine = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Waive Fine"
    )


class UserRegistrationForm(forms.ModelForm):
    """Form for initial user registration."""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

