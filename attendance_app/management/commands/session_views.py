import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from attendance_app.models import ClassSession, Course
from attendance_app.decorators import teacher_required


@login_required
@teacher_required
def create_session(request):
    if request.method == 'POST':
        course_id = request.POST.get('course')
        date_str = request.POST.get('date')
        time_slot = request.POST.get('time_slot')
        room_number = request.POST.get('room_number')

        try:
            course = Course.objects.get(id=course_id)
            session_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Generate a unique QR code
            dynamic_qr_code = f"{uuid.uuid4().hex[:8].upper()}"

            # Parse time slot to calculate QR validity
            start_time_str, end_time_str = time_slot.split('-')
            start_time = datetime.strptime(start_time_str.strip(), '%H:%M').time()
            end_time = datetime.strptime(end_time_str.strip(), '%H:%M').time()

            # Combine date and time
            start_datetime = timezone.make_aware(datetime.combine(session_date, start_time))
            end_datetime = timezone.make_aware(datetime.combine(session_date, end_time))

            # QR validity (15 min before and after session)
            qr_validity_start = start_datetime - timedelta(minutes=15)
            qr_validity_end = end_datetime + timedelta(minutes=15)

            # Determine initial status based on current time
            now = timezone.now()
            if now > end_datetime:
                status = 'Completed'
            elif now >= start_datetime:
                status = 'Ongoing'
            else:
                status = 'Scheduled'

            # Create the session
            ClassSession.objects.create(
                course=course,
                teacher=request.user.teacher,
                date=session_date,
                time_slot=time_slot,
                room_number=room_number,
                dynamic_qr_code=dynamic_qr_code,
                qr_validity_start=qr_validity_start,
                qr_validity_end=qr_validity_end,
                session_status=status
            )

            messages.success(request, 'Session created successfully!')
            return redirect('teacher_dashboard')

        except Course.DoesNotExist:
            messages.error(request, 'Course not found.')
        except ValueError as e:
            messages.error(request, f'Invalid form data: {str(e)}')

    # GET request - just show the form
    courses = Course.objects.filter(department=request.user.teacher.department)
    return render(request, 'attendance_app/session/create_session.html', {
        'courses': courses
    })
