from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_ticket_location_ticket_session_key_alter_ticket_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='ticket_type',
            field=models.CharField(
                choices=[('issue', 'Issue'), ('request', 'Request')],
                default='issue',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='ticket',
            name='requested_items',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
