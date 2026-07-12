from django.contrib import admin
from django.utils.html import format_html
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    # ------------------------------------------------------------------
    # List view configuration
    # ------------------------------------------------------------------
    list_display = (
        'id', 'title', 'ticket_type', 'name', 'location',
        'colored_status', 'priority_badge', 'created_at',
    )
    list_display_links = ('id', 'title')
    list_filter = ('ticket_type', 'status', 'priority', 'created_at')
    search_fields = ('title', 'name', 'location', 'description')
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'

    # ------------------------------------------------------------------
    # Detail / edit view configuration
    # ------------------------------------------------------------------
    fieldsets = (
        ('Ticket Info', {
            'fields': (
                'title', 'ticket_type', 'requested_items', 'name', 'location',
                'description', 'priority',
            ),
        }),
        ('Status Management', {
            'fields': ('status',),
            'description': 'Only admins can update the status of a ticket.',
        }),
        ('Metadata', {
            'fields': ('session_key', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('session_key', 'created_at', 'updated_at')

    # ------------------------------------------------------------------
    # Bulk actions
    # ------------------------------------------------------------------
    actions = ['mark_in_progress', 'mark_resolved', 'mark_open']

    @admin.action(description='Mark selected tickets as In Progress')
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} ticket(s) marked as In Progress.')

    @admin.action(description='Mark selected tickets as Resolved')
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} ticket(s) marked as Resolved.')

    @admin.action(description='Mark selected tickets as Open')
    def mark_open(self, request, queryset):
        updated = queryset.update(status='open')
        self.message_user(request, f'{updated} ticket(s) marked as Open.')

    # ------------------------------------------------------------------
    # Custom display columns
    # ------------------------------------------------------------------
    @admin.display(description='Status', ordering='status')
    def colored_status(self, obj):
        colors = {
            'open': ('#06b6d4', '#0e2a30'),
            'in_progress': ('#f59e0b', '#2e1f05'),
            'resolved': ('#10b981', '#052e1c'),
        }
        labels = {
            'open': 'Open',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
        }
        color, bg = colors.get(obj.status, ('#94a3b8', '#1e293b'))
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="'
            'background:{bg}; color:{color}; padding:3px 10px; '
            'border-radius:20px; font-size:0.78rem; font-weight:600; '
            'letter-spacing:0.05em; text-transform:uppercase;">'
            '{label}</span>',
            bg=bg, color=color, label=label,
        )

    @admin.display(description='Priority', ordering='priority')
    def priority_badge(self, obj):
        colors = {
            'high': ('#ef4444', '#2d0a0a'),
            'medium': ('#f59e0b', '#2e1f05'),
            'low': ('#64748b', '#1e293b'),
        }
        color, bg = colors.get(obj.priority, ('#94a3b8', '#1e293b'))
        return format_html(
            '<span style="'
            'background:{bg}; color:{color}; padding:3px 10px; '
            'border-radius:20px; font-size:0.78rem; font-weight:600; '
            'letter-spacing:0.05em; text-transform:uppercase;">'
            '{priority}</span>',
            bg=bg, color=color, priority=obj.priority.capitalize(),
        )
