from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    """
    Customer-facing serializer.
    - `status` and `session_key` are read-only: customers cannot set or change
      the ticket status; the admin does that via Django Admin.
    - `session_key` is write-only on creation only (handled in the view's
      perform_create) and never exposed in responses.
    """

    class Meta:
        model = Ticket
        fields = [
            'id',
            'title',
            'name',
            'location',
            'description',
            'status',
            'priority',
            'session_key',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'session_key', 'created_at', 'updated_at']
        extra_kwargs = {
            # Never expose the session_key in API responses for security
            'session_key': {'write_only': True},
        }
