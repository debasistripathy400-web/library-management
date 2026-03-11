"""
Admin configuration for the Library Management System.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Book, Member, Transaction, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'quantity', 'available', 'is_available_badge', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'author', 'isbn')
    readonly_fields = ('created_at', 'updated_at')

    def is_available_badge(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green; font-weight: bold;">✔ Available</span>')
        return format_html('<span style="color: red; font-weight: bold;">✘ Not Available</span>')
    is_available_badge.short_description = 'Availability'


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'name', 'email', 'phone', 'join_date', 'is_active', 'active_borrows')
    list_filter = ('is_active', 'join_date')
    search_fields = ('name', 'email', 'member_id', 'phone')
    readonly_fields = ('member_id', 'join_date')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'member', 'issue_date', 'due_date', 'return_date', 'status', 'fine_amount')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('book__title', 'member__name', 'member__member_id')
    readonly_fields = ('issue_date',)


# Customize admin site header
admin.site.site_header = "Library Management System"
admin.site.site_title = "LMS Admin"
admin.site.index_title = "Welcome to LMS Admin Panel"
