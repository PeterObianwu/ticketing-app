from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Ticket
from .serializers import TicketSerializer

# Header name used to carry the browser-generated session key
SESSION_KEY_HEADER = 'HTTP_X_SESSION_KEY'


class DashboardView(TemplateView):
    template_name = 'tickets/index.html'


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer

    def get_session_key(self):
        """Return the session key from the custom request header, or empty string."""
        return self.request.META.get(SESSION_KEY_HEADER, '').strip()

    def get_queryset(self):
        session_key = self.get_session_key()

        # Only return tickets belonging to the requesting browser session.
        # If no session key is present, return an empty queryset so nothing leaks.
        if not session_key:
            queryset = Ticket.objects.none()
        else:
            queryset = Ticket.objects.filter(session_key=session_key)

        status = self.request.query_params.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        ordering = self.request.query_params.get('ordering')
        if ordering:
            if ordering == 'newest':
                queryset = queryset.order_by('-created_at')
            elif ordering == 'oldest':
                queryset = queryset.order_by('created_at')
            elif ordering == 'priority-desc':
                queryset = queryset.annotate(
                    priority_order=Case(
                        When(priority='high', then=Value(3)),
                        When(priority='medium', then=Value(2)),
                        When(priority='low', then=Value(1)),
                        output_field=IntegerField(),
                    )
                ).order_by('-priority_order', '-created_at')
            elif ordering == 'priority-asc':
                queryset = queryset.annotate(
                    priority_order=Case(
                        When(priority='high', then=Value(3)),
                        When(priority='medium', then=Value(2)),
                        When(priority='low', then=Value(1)),
                        output_field=IntegerField(),
                    )
                ).order_by('priority_order', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def perform_create(self, serializer):
        """
        Attach the session_key from the request header when saving a new ticket.
        Status is always forced to 'open' — only admins can change it.
        """
        session_key = self.get_session_key()
        serializer.save(status='open', session_key=session_key)

    def partial_update(self, request, *args, **kwargs):
        """
        Override PATCH to strip `status` and `session_key` from customer requests.
        Customers can update title, description, priority, name, location — not status.
        """
        # Remove protected fields that only admins can change
        mutable_data = {
            k: v for k, v in request.data.items()
            if k not in ('status', 'session_key')
        }
        kwargs['partial'] = True
        # Temporarily replace request.data with filtered data
        request._full_data = mutable_data
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return ticket counts scoped to the current session."""
        session_key = self.get_session_key()
        if not session_key:
            return Response({'total': 0, 'open': 0, 'in_progress': 0, 'resolved': 0})

        base_qs = Ticket.objects.filter(session_key=session_key)
        total = base_qs.count()
        open_count = base_qs.filter(status='open').count()
        in_progress = base_qs.filter(status='in_progress').count()
        resolved = base_qs.filter(status='resolved').count()
        return Response({
            'total': total,
            'open': open_count,
            'in_progress': in_progress,
            'resolved': resolved,
        })
