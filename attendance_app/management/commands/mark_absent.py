from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance_app.models import ClassSession, Attendance, Student


class Command(BaseCommand):
    help = 'Mark absent for students who did not attend a completed session'

    def handle(self, *args, **options):
        # Get completed sessions that ended in the last 24 hours
        yesterday = timezone.now() - timezone.timedelta(days=1)
        sessions = ClassSession.objects.filter(
            session_status='Completed',
            qr_validity_end__gte=yesterday
        )

        marked_count = 0
        for session in sessions:
            # Get all students who should have attended but didn't
            students = Student.objects.all()
            for student in students:
                # Check if the student already has an attendance record for this session
                if not Attendance.objects.filter(session=session, student=student).exists():
                    # Mark as absent
                    Attendance.objects.create(
                        student=student,
                        session=session,
                        timestamp=session.qr_validity_end,
                        attendance_status="Absent",
                        qr_verification_status="Invalid"
                    )
                    marked_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully marked {marked_count} absent records")
        )
