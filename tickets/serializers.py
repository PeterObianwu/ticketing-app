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
            'ticket_type',
            'requested_items',
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
            'title': {'required': False},
            # Never expose the session_key in API responses for security
            'session_key': {'write_only': True},
        }

    def validate(self, attrs):
        ticket_type = attrs.get(
            'ticket_type', getattr(self.instance, 'ticket_type', 'issue')
        )
        requested_items = attrs.get(
            'requested_items', getattr(self.instance, 'requested_items', [])
        )
        allowed_items = {
            'laptop', 'mouse', 'signature_pad', 'barcode_scanner',
            'ticket_printer', 'a4_printer',
        }

        if ticket_type == 'request':
            if not isinstance(requested_items, list) or not requested_items:
                raise serializers.ValidationError({
                    'requested_items': 'Select at least one requested item.'
                })
            if set(requested_items) - allowed_items:
                raise serializers.ValidationError({
                    'requested_items': 'One or more selected items are invalid.'
                })
        else:
            attrs['requested_items'] = []

        if self.instance is None and not attrs.get('title'):
            if ticket_type == 'request':
                labels = {
                    'laptop': 'Laptop',
                    'mouse': 'Mouse',
                    'signature_pad': 'Signature pad',
                    'barcode_scanner': 'Barcode scanner',
                    'ticket_printer': 'Ticket printer',
                    'a4_printer': 'A4 printer',
                }
                items = ', '.join(labels[item] for item in requested_items)
                attrs['title'] = f'Request: {items}'[:200]
            else:
                description = attrs.get('description', '').strip()
                attrs['title'] = description[:80] or 'Issue'
        return attrs
