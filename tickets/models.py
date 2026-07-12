from django.db import models


class Ticket(models.Model):
    TICKET_TYPE_CHOICES = [
        ('issue', 'Issue'),
        ('request', 'Request'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=200)
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPE_CHOICES, default='issue')
    requested_items = models.JSONField(blank=True, default=list)
    name = models.CharField(max_length=200, blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    # Stores the browser-generated UUID from localStorage — used to scope
    # ticket visibility so each customer only sees their own submissions.
    session_key = models.CharField(max_length=64, blank=True, default='', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
