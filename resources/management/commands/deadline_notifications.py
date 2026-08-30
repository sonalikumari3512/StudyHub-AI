from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from resources.models import Assignment
from users.models import Notification


class Command(BaseCommand):

    help = "Create notifications for assignments due within 24 hours."

    def handle(self, *args, **kwargs):

        now = timezone.now()
        tomorrow = now + timedelta(hours=24)

        assignments = Assignment.objects.filter(
            due_date__gt=now,
            due_date__lte=tomorrow
        ).select_related("room")

        notification_count = 0

        for assignment in assignments:

            room = assignment.room

            # Get all students/members except assignment creator
            members = room.members.exclude(
                id=assignment.created_by.id
            )

            for member in members:

                # Prevent duplicate deadline notifications
                already_notified = Notification.objects.filter(
                    user=member,
                    notification_type="deadline",
                    link=f"/rooms/{room.id}/assignments/{assignment.id}/"
                ).exists()

                if already_notified:
                    continue

                Notification.objects.create(
                    user=member,
                    title="⏰ Assignment Deadline",
                    message=(
                        f"'{assignment.title}' in {room.name} "
                        f"is due within 24 hours."
                    ),
                    notification_type="deadline",
                    link=f"/rooms/{room.id}/assignments/{assignment.id}/",
                )

                notification_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {notification_count} deadline notification(s)."
            )
        )

