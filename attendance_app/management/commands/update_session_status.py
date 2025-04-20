from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance_app.models import ClassSession
from datetime import datetime


class Command(BaseCommand):
    help = 'Updates session statuses based on current time'

    def handle(self, *args, **options):
        now = timezone.now()
        sessions = ClassSession.objects.all()
        scheduled_count = 0
        ongoing_count = 0
        completed_count = 0

        for session in sessions:
            # Parse time_slot (format: "10:00-11:00")
            try:
                start_time_str, end_time_str = session.time_slot.split('-')
                start_time = datetime.strptime(start_time_str.strip(), '%H:%M').time()
                end_time = datetime.strptime(end_time_str.strip(), '%H:%M').time()

                # Create datetime objects for session start and end
                session_start = datetime.combine(session.date, start_time)
                session_end = datetime.combine(session.date, end_time)

                # Make timezone aware
                session_start = timezone.make_aware(session_start)
                session_end = timezone.make_aware(session_end)

                # Update status based on current time
                if now > session_end:
                    # Session has ended
                    if session.session_status != 'Completed':
                        session.session_status = 'Completed'
                        session.save(update_fields=['session_status'])
                        completed_count += 1
                elif now >= session_start:
                    # Session is currently ongoing
                    if session.session_status != 'Ongoing':
                        session.session_status = 'Ongoing'
                        session.save(update_fields=['session_status'])
                        ongoing_count += 1
                else:
                    # Session is in the future
                    if session.session_status != 'Scheduled':
                        session.session_status = 'Scheduled'
                        session.save(update_fields=['session_status'])
                        scheduled_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error updating session {session.id}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated statuses: {scheduled_count} scheduled, {ongoing_count} ongoing, {completed_count} completed")
        )
