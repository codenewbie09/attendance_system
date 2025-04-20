from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import ClassSession, Attendance, Student, Course
from ..decorators import admin_required, teacher_required, student_required
import qrcode
from io import BytesIO
import uuid
import random
import string


def help(request):
    return render(request, 'attendance_app/help.html')

@login_required
def home(request):
    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    elif request.user.user_type == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')


@login_required
@admin_required
def admin_dashboard(request):
    sessions = ClassSession.objects.all().order_by('-date')
    ongoing_count = sessions.filter(session_status='Ongoing').count()
    completed_count = sessions.filter(session_status='Completed').count()
    total_count = sessions.count()
    return render(request, 'attendance_app/dashboard/admin_dashboard.html', {
        'sessions': sessions,
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'total_count': total_count,
    })


@login_required
@teacher_required
def teacher_dashboard(request):
    teacher = request.user.teacher
    sessions = ClassSession.objects.filter(teacher=teacher).order_by('-date')
    ongoing_count = sessions.filter(session_status='Ongoing').count()
    completed_count = sessions.filter(session_status='Completed').count()
    total_count = sessions.count()
    return render(request, 'attendance_app/dashboard/teacher_dashboard.html', {
        'sessions': sessions,
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'total_count': total_count,
    })


@login_required
@student_required
def student_dashboard(request):
    student = request.user.student
    attendance_records = Attendance.objects.filter(
        student=student
    ).select_related('session__course').order_by('-timestamp')

    # Calculate attendance percentage
    total_sessions = ClassSession.objects.filter(
        session_status__in=['Ongoing', 'Completed']
    ).count()

    if total_sessions > 0:
        attended_sessions = attendance_records.filter(
            attendance_status__in=['Present', 'Late']
        ).count()
        attendance_percentage = (attended_sessions / total_sessions) * 100
    else:
        attendance_percentage = 0

    return render(request, 'attendance_app/dashboard/student_dashboard.html', {
        'attendance_records': attendance_records[:10],  # Show only last 10 records
        'attendance_percentage': attendance_percentage,
    })


@login_required
@teacher_required
def create_session(request):
    if request.method == 'POST':
        # Process form data
        course_id = request.POST.get('course')
        date = request.POST.get('date')
        time_slot = request.POST.get('time_slot')
        room_number = request.POST.get('room_number')

        # Generate a random dynamic QR code
        dynamic_qr_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        # Set validity period (e.g., 15 minutes from now)
        now = timezone.now()
        validity_start = now
        validity_end = now + timezone.timedelta(minutes=15)

        ClassSession.objects.create(
            course_id=course_id,
            teacher=request.user.teacher,
            date=date,
            time_slot=time_slot,
            room_number=room_number,
            dynamic_qr_code=dynamic_qr_code,
            qr_validity_start=validity_start,
            qr_validity_end=validity_end,
            session_status='Scheduled'
        )
        return redirect('teacher_dashboard')
    else:
        # Provide form
        courses = Course.objects.all()
        return render(request, 'attendance_app/session/create_session.html', {'courses': courses})


@login_required
@teacher_required
def generate_qr(request, session_id):
    session = get_object_or_404(ClassSession, pk=session_id)

    # Verify that the requesting teacher is the one who created the session
    if session.teacher.user != request.user:
        return HttpResponseForbidden("You don't have permission to access this QR code.")

    # Update QR code and validity period
    now = timezone.now()
    session.dynamic_qr_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    session.qr_validity_start = now
    session.qr_validity_end = now + timezone.timedelta(minutes=15)
    session.save()

    # Generate QR code
    qr_data = f"{session.id}-{session.dynamic_qr_code}"
    img = qrcode.make(qr_data)

    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


@login_required
@teacher_required
def show_qr_page(request, session_id):
    session = get_object_or_404(ClassSession, pk=session_id)

    # Verify that the requesting teacher is the one who created the session
    if session.teacher.user != request.user:
        return HttpResponseForbidden("You don't have permission to access this QR code.")

    return render(request, 'attendance_app/session/show_qr.html', {'session': session})
