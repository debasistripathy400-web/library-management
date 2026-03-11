"""
Models for the Library Management System.
Defines Books, Members, and Transactions tables.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Category(models.Model):
    """Book categories (e.g., Science, Fiction, History)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """Represents a book in the library."""
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    available = models.PositiveIntegerField(default=1)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def is_available(self):
        return self.available > 0

    @property
    def issued_count(self):
        return self.quantity - self.available


class Member(models.Model):
    """Represents a library member."""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    member_id = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    join_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        # Auto-generate member ID
        if not self.member_id:
            last = Member.objects.order_by('-id').first()
            last_id = last.id if last else 0
            self.member_id = f"LIB{str(last_id + 1).zfill(4)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member_id} - {self.name}"

    @property
    def active_borrows(self):
        return self.transactions.filter(status__in=['issued', 'overdue']).count()

    @property
    def total_borrows(self):
        return self.transactions.count()


class Transaction(models.Model):
    """Tracks book issue and return transactions."""
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='transactions')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='transactions')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    fine_per_day = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='issued')
    remarks = models.TextField(blank=True)
    issued_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_transactions'
    )

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"TXN-{self.id} | {self.book.title} → {self.member.name}"

    def calculate_fine(self):
        """Calculate fine for overdue books."""
        if self.return_date:
            overdue_days = (self.return_date - self.due_date).days
        else:
            overdue_days = (timezone.now().date() - self.due_date).days
        if overdue_days > 0:
            return overdue_days * float(self.fine_per_day)
        return 0.0

    @property
    def is_overdue(self):
        if self.status == 'returned':
            return False
        return timezone.now().date() > self.due_date

    @property
    def days_remaining(self):
        if self.status == 'returned':
            return None
        remaining = (self.due_date - timezone.now().date()).days
        return remaining
