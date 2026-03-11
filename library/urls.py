"""
URL patterns for the Library Management System.
"""

from django.urls import path
from . import views

urlpatterns = [
    # ─── Public Pages ───
    path('', views.landing_page, name='home'),
    path('register/', views.register_view, name='register'),

    # ─── Authentication ───
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ─── Dashboard ───
    path('dashboard/', views.dashboard, name='dashboard'),

    # ─── Books ───
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete, name='book_delete'),

    # ─── Categories ───
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # ─── Members ───
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.member_add, name='member_add'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),

    # ─── Transactions ───
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/issue/', views.issue_book, name='issue_book'),
    path('transactions/<int:pk>/return/', views.return_book, name='return_book'),

    # ─── Reports ───
    path('reports/', views.report_dashboard, name='report_dashboard'),
    path('reports/overdue/', views.overdue_report, name='overdue_report'),
    path('reports/export/transactions/', views.export_transactions_csv, name='export_transactions'),

    # ─── Member Portal ───
    path('portal/', views.member_portal, name='member_portal'),
    path('portal/search/', views.member_search_books, name='member_search'),
]
