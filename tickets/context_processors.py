from django.db.models import Count, Q

from .models import Ticket


def admin_ticket_stats(request):
    """Expose ticket totals only to the admin dashboard template."""
    if request.path.rstrip('/') != '/admin' or not request.user.is_staff:
        return {}

    return {
        'stats': Ticket.objects.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            resolved=Count('id', filter=Q(status='resolved')),
        )
    }
