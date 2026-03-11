"""
Views for the Library Management System.
Handles all CRUD operations for books, members, transactions, auth, and reports.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
import csv

from .models import Book, Member, Transaction, Category
from .forms import (
    LoginForm, BookForm, BookSearchForm, MemberForm,
    MemberUserForm, IssueBookForm, ReturnBookForm, CategoryForm,
    UserRegistrationForm
)


# ─────────────────────────────────────────────────────────────
# Helper: Check if user is staff/admin
# ─────────────────────────────────────────────────────────────
def is_admin(user):
    return user.is_authenticated and user.is_staff


def admin_required(view_func):
    """Decorator: redirects non-admin users to login."""
    return login_required(user_passes_test(is_admin, login_url='/login/')(view_func))


# ─────────────────────────────────────────────────────────────
# Authentication Views
# ─────────────────────────────────────────────────────────────
def login_view(request):
    """Admin login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'library/login.html', {'form': form})


def logout_view(request):
    """Logout and redirect to login."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


def register_view(request):
    """Member registration page."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['name']
            )
            # Create member profile
            Member.objects.create(
                user=user,
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone']
            )
            messages.success(request, "Registration successful! Please login.")
            return redirect('login')
    return render(request, 'library/register.html', {'form': form})


def landing_page(request):
    """The home page of the library."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    recent_books = Book.objects.order_by('-created_at')[:4]
    categories = Category.objects.all()[:6]
    
    context = {
        'recent_books': recent_books,
        'categories': categories,
    }
    return render(request, 'library/landing.html', context)



# ─────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    """Main dashboard with statistics."""
    total_books = Book.objects.count()
    total_members = Member.objects.filter(is_active=True).count()
    total_issued = Transaction.objects.filter(status__in=['issued', 'overdue']).count()
    total_categories = Category.objects.count()

    # Overdue transactions
    today = timezone.now().date()
    overdue_count = Transaction.objects.filter(
        status='issued',
        due_date__lt=today
    ).count()

    # Update overdue statuses
    Transaction.objects.filter(status='issued', due_date__lt=today).update(status='overdue')

    # Recent transactions
    recent_transactions = Transaction.objects.select_related('book', 'member').order_by('-id')[:8]

    # Recently added books
    recent_books = Book.objects.order_by('-created_at')[:5]

    # Top borrowed books
    top_books = Book.objects.annotate(
        borrow_count=Count('transactions')
    ).order_by('-borrow_count')[:5]

    context = {
        'total_books': total_books,
        'total_members': total_members,
        'total_issued': total_issued,
        'total_categories': total_categories,
        'overdue_count': overdue_count,
        'recent_transactions': recent_transactions,
        'recent_books': recent_books,
        'top_books': top_books,
    }
    return render(request, 'library/dashboard.html', context)


# ─────────────────────────────────────────────────────────────
# Book Views
# ─────────────────────────────────────────────────────────────
@login_required
def book_list(request):
    """List all books with search functionality."""
    query = request.GET.get('query', '')
    category_id = request.GET.get('category', '')
    availability = request.GET.get('availability', '')

    books = Book.objects.select_related('category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )
    if category_id:
        books = books.filter(category_id=category_id)
    if availability == 'available':
        books = books.filter(available__gt=0)
    elif availability == 'issued':
        books = books.filter(available=0)

    categories = Category.objects.all()
    context = {
        'books': books,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'availability': availability,
        'total': books.count(),
    }
    return render(request, 'library/books/book_list.html', context)


@admin_required
def book_add(request):
    """Add a new book."""
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' added successfully!")
            return redirect('book_list')
    return render(request, 'library/books/book_form.html', {'form': form, 'title': 'Add New Book'})


@admin_required
def book_edit(request, pk):
    """Edit an existing book."""
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, request.FILES or None, instance=book)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"Book '{book.title}' updated successfully!")
            return redirect('book_list')
    return render(request, 'library/books/book_form.html', {'form': form, 'title': 'Edit Book', 'book': book})


@admin_required
def book_delete(request, pk):
    """Delete a book."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        # Check if it has active transactions
        if book.transactions.filter(status__in=['issued', 'overdue']).exists():
            messages.error(request, f"Cannot delete '{book.title}'. It has active issued transactions.")
            return redirect('book_list')
        title = book.title
        book.delete()
        messages.success(request, f"Book '{title}' deleted successfully!")
        return redirect('book_list')
    return render(request, 'library/books/book_confirm_delete.html', {'book': book})


@login_required
def book_detail(request, pk):
    """View book details and transaction history."""
    book = get_object_or_404(Book, pk=pk)
    transactions = book.transactions.select_related('member').order_by('-issue_date')[:10]
    return render(request, 'library/books/book_detail.html', {'book': book, 'transactions': transactions})


# ─────────────────────────────────────────────────────────────
# Category Views
# ─────────────────────────────────────────────────────────────
@admin_required
def category_list(request):
    """Manage book categories."""
    categories = Category.objects.annotate(book_count=Count('books'))
    form = CategoryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully!")
            return redirect('category_list')
    return render(request, 'library/books/category_list.html', {'categories': categories, 'form': form})


@admin_required
def category_delete(request, pk):
    """Delete a category."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted.")
        return redirect('category_list')
    return redirect('category_list')


# ─────────────────────────────────────────────────────────────
# Member Views
# ─────────────────────────────────────────────────────────────
@admin_required
def member_list(request):
    """List all library members."""
    query = request.GET.get('query', '')
    members = Member.objects.all()
    if query:
        members = members.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(member_id__icontains=query) |
            Q(phone__icontains=query)
        )
    context = {'members': members, 'query': query}
    return render(request, 'library/members/member_list.html', context)


@admin_required
def member_add(request):
    """Register a new member."""
    form = MemberForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Member '{member.name}' (ID: {member.member_id}) registered!")
            return redirect('member_list')
    return render(request, 'library/members/member_form.html', {'form': form, 'title': 'Register New Member'})


@admin_required
def member_edit(request, pk):
    """Edit member details."""
    member = get_object_or_404(Member, pk=pk)
    form = MemberForm(request.POST or None, request.FILES or None, instance=member)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"Member '{member.name}' updated successfully!")
            return redirect('member_detail', pk=member.pk)
    return render(request, 'library/members/member_form.html', {
        'form': form, 'title': 'Edit Member', 'member': member
    })


@admin_required
def member_delete(request, pk):
    """Delete a member."""
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        if member.transactions.filter(status__in=['issued', 'overdue']).exists():
            messages.error(request, f"Cannot delete '{member.name}'. Member has active borrowed books.")
            return redirect('member_list')
        name = member.name
        member.delete()
        messages.success(request, f"Member '{name}' deleted.")
        return redirect('member_list')
    return render(request, 'library/members/member_confirm_delete.html', {'member': member})


@login_required
def member_detail(request, pk):
    """View member details and borrowing history."""
    member = get_object_or_404(Member, pk=pk)
    transactions = member.transactions.select_related('book').order_by('-issue_date')
    active = transactions.filter(status__in=['issued', 'overdue'])
    history = transactions.filter(status='returned')
    context = {
        'member': member,
        'active_transactions': active,
        'history': history,
    }
    return render(request, 'library/members/member_detail.html', context)


# ─────────────────────────────────────────────────────────────
# Transaction Views
# ─────────────────────────────────────────────────────────────
@admin_required
def transaction_list(request):
    """View all transactions."""
    status_filter = request.GET.get('status', '')
    transactions = Transaction.objects.select_related('book', 'member').all()

    # Auto-update overdue
    today = timezone.now().date()
    Transaction.objects.filter(status='issued', due_date__lt=today).update(status='overdue')

    if status_filter:
        transactions = transactions.filter(status=status_filter)

    context = {
        'transactions': transactions,
        'status_filter': status_filter,
        'issued_count': Transaction.objects.filter(status='issued').count(),
        'overdue_count': Transaction.objects.filter(status='overdue').count(),
        'returned_count': Transaction.objects.filter(status='returned').count(),
    }
    return render(request, 'library/transactions/transaction_list.html', context)


@admin_required
def issue_book(request):
    """Issue a book to a member."""
    form = IssueBookForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.issued_by = request.user
            # Decrease available count
            book = transaction.book
            if book.available <= 0:
                messages.error(request, f"'{book.title}' is not available.")
                return render(request, 'library/transactions/issue_book.html', {'form': form})
            book.available -= 1
            book.save()
            transaction.save()
            messages.success(
                request,
                f"Book '{book.title}' issued to {transaction.member.name}. Due: {transaction.due_date}"
            )
            return redirect('transaction_list')
    return render(request, 'library/transactions/issue_book.html', {'form': form})


@admin_required
def return_book(request, pk):
    """Process book return."""
    transaction = get_object_or_404(Transaction, pk=pk)

    if transaction.status == 'returned':
        messages.warning(request, "This book has already been returned.")
        return redirect('transaction_list')

    fine = transaction.calculate_fine()
    form = ReturnBookForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            transaction.return_date = timezone.now().date()
            transaction.status = 'returned'
            waive_fine = form.cleaned_data.get('waive_fine', False)
            if waive_fine:
                transaction.fine_amount = 0
            else:
                transaction.fine_amount = fine
            if form.cleaned_data.get('remarks'):
                transaction.remarks = form.cleaned_data['remarks']
            transaction.save()

            # Increase book availability
            book = transaction.book
            book.available += 1
            book.save()

            messages.success(
                request,
                f"Book '{book.title}' returned by {transaction.member.name}. Fine: ₹{transaction.fine_amount}"
            )
            return redirect('transaction_list')

    context = {
        'transaction': transaction,
        'fine': fine,
        'form': form,
    }
    return render(request, 'library/transactions/return_book.html', context)


# ─────────────────────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────────────────────
@admin_required
def overdue_report(request):
    """Overdue books report."""
    today = timezone.now().date()
    # Update statuses
    Transaction.objects.filter(status='issued', due_date__lt=today).update(status='overdue')

    overdue = Transaction.objects.filter(status='overdue').select_related('book', 'member').order_by('due_date')

    # Calculate fines
    for t in overdue:
        t.calculated_fine = t.calculate_fine()

    context = {'overdue_transactions': overdue, 'today': today}
    return render(request, 'library/reports/overdue_report.html', context)


@admin_required
def report_dashboard(request):
    """General report dashboard."""
    today = timezone.now().date()
    books_by_category = Category.objects.annotate(count=Count('books'))
    monthly_issues = Transaction.objects.filter(
        issue_date__month=today.month, issue_date__year=today.year
    ).count()
    monthly_returns = Transaction.objects.filter(
        return_date__month=today.month, return_date__year=today.year
    ).count()
    total_fines = Transaction.objects.filter(status='returned').aggregate(
        total=Sum('fine_amount')
    )['total'] or 0

    context = {
        'books_by_category': books_by_category,
        'monthly_issues': monthly_issues,
        'monthly_returns': monthly_returns,
        'total_fines': total_fines,
        'today': today,
    }
    return render(request, 'library/reports/report_dashboard.html', context)


@admin_required
def export_transactions_csv(request):
    """Export all transactions as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Book', 'Member', 'Issue Date', 'Due Date', 'Return Date', 'Status', 'Fine'])

    for t in Transaction.objects.select_related('book', 'member').all():
        writer.writerow([
            t.id, t.book.title, t.member.name,
            t.issue_date, t.due_date, t.return_date or '',
            t.status, t.fine_amount
        ])
    return response


# ─────────────────────────────────────────────────────────────
# Member Portal (for logged-in members)
# ─────────────────────────────────────────────────────────────
@login_required
def member_portal(request):
    """Member's personal dashboard."""
    try:
        member = request.user.member
    except Member.DoesNotExist:
        messages.error(request, "No member profile found for your account.")
        return redirect('dashboard')

    active_txn = member.transactions.filter(
        status__in=['issued', 'overdue']
    ).select_related('book')
    history = member.transactions.filter(status='returned').select_related('book')[:10]

    context = {'member': member, 'active_transactions': active_txn, 'history': history}
    return render(request, 'library/member_portal/portal.html', context)


@login_required
def member_search_books(request):
    """Member can search for available books."""
    query = request.GET.get('query', '')
    category_id = request.GET.get('category', '')
    books = Book.objects.filter(available__gt=0)

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query)
        )
    if category_id:
        books = books.filter(category_id=category_id)

    categories = Category.objects.all()
    context = {'books': books, 'categories': categories, 'query': query}
    return render(request, 'library/member_portal/search_books.html', context)
