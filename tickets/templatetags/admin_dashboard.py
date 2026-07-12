from django import template
from django.db.models import Count, Q

from tickets.models import Ticket


register = template.Library()


@register.simple_tag
def ticket_stats():
    return Ticket.objects.aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        resolved=Count('id', filter=Q(status='resolved')),
    )
