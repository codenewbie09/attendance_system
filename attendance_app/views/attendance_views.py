from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
from ..models import ClassSession, Attendance, Student
from ..decorators import admin_required, teacher_required, student_required
from django.contrib import messages
import csv


@login_required
@student_required
def mark_attendance(request, session_id):
    session = get_object_or_404(ClassSession, pk=session_id)

    # Check if the QR code is still valid
    if not session.is_valid():
        return render(request, 'attendance_app/attendance/invalid_qr.html')

    # Check if attendance already marked
    student = request.user.student
    existing_attendance = Attendance.objects.filter(student=student, session=session).exists()

    if existing_attendance:
        return render(request, 'attendance_app/attendance/already_marked.html')

    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')

        # Verify QR code
        expected_qr_data = f"{session.id}-{session.dynamic_qr_code}"
        if qr_code == expected_qr_data:
            # Mark attendance
            Attendance.objects.create(
                student=student,
                session=session,
                attendance_status='Present',
                qr_verification_status='Valid',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return render(request, 'attendance_app/attendance/success.html')
        else:
            return render(request, 'attendance_app/attendance/invalid_code.html')

    return render(request, 'attendance_app/attendance/mark_attendance.html', {'session': session})


# attendance_app/views/attendance_views.py
@login_required
@teacher_required
def attendance_report(request, session_id):
    session = get_object_or_404(ClassSession, pk=session_id)
    records = Attendance.objects.filter(session=session).select_related('student')

    # Calculate counts here
    present_count = records.filter(attendance_status='Present').count()
    absent_count = records.filter(attendance_status='Absent').count()
    late_count = records.filter(attendance_status='Late').count()

    return render(request, 'attendance_app/reports/attendance_report.html', {
        'session': session,
        'records': records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
    })


@login_required
@admin_required
def admin_attendance_report(request, session_id=None):
    if session_id:
        session = get_object_or_404(ClassSession, pk=session_id)
        records = Attendance.objects.filter(session=session).select_related('student')
        return render(request, 'attendance_app/reports/admin_attendance_report.html',
                      {'session': session, 'records': records})
    else:
        sessions = ClassSession.objects.all().order_by('-date')
        return render(request, 'attendance_app/reports/admin_sessions.html', {'sessions': sessions})


@login_required
@student_required
def student_attendance_summary(request):
    student = request.user.student
    attendance_records = Attendance.objects.filter(student=student).select_related('session')

    # Calculate attendance percentage by course
    course_attendance = {}
    for record in attendance_records:
        course = record.session.course
        if course.id not in course_attendance:
            course_attendance[course.id] = {
                'course': course,
                'present': 0,
                'total': 0,
                'percentage': 0
            }

        course_attendance[course.id]['total'] += 1
        if record.attendance_status == 'Present':
            course_attendance[course.id]['present'] += 1

    # Calculate percentages
    for course_id in course_attendance:
        present = course_attendance[course_id]['present']
        total = course_attendance[course_id]['total']
        course_attendance[course_id]['percentage'] = (present / total * 100) if total > 0 else 0

    return render(request, 'attendance_app/reports/student_summary.html',
                  {'course_attendance': course_attendance.values()})


@login_required
@teacher_required
def export_attendance_csv(request, session_id):
    session = get_object_or_404(ClassSession, pk=session_id)

    # Verify that the requesting teacher is the one who created the session
    if session.teacher.user != request.user:
        return HttpResponseForbidden("You don't have permission to export this data.")

    records = Attendance.objects.filter(session=session).select_related('student')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_session_{session_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Student Name', 'Attendance Status', 'Timestamp', 'IP Address'])

    for record in records:
        writer.writerow([
            record.student.roll_no,
            record.student.name,
            record.attendance_status,
            record.timestamp,
            record.ip_address
        ])

    return response


@login_required
@student_required
def process_session_id(request):
    if request.method == "POST":
        session_id = request.POST.get('session_id')
        qr_code = request.POST.get('qr_code')

        # Validate inputs
        if not session_id or not qr_code:
            messages.error(request, "Both Session ID and QR Code are required.")
            return redirect('student_dashboard')

        try:
            session = ClassSession.objects.get(id=session_id)
        except ClassSession.DoesNotExist:
            messages.error(request, "Session not found.")
            return redirect('student_dashboard')

        # Debug info - print both values for comparison
        print("Entered QR code:", qr_code)
        print("Session QR code:", session.dynamic_qr_code)

        # Robust comparison - ignore case and whitespace
        if session.dynamic_qr_code.strip().upper() != qr_code.strip().upper():
            messages.error(request, "Invalid QR code for this session.")
            return redirect('student_dashboard')

        # Get current time
        now = timezone.now()

        # Parse time slot to get session end time
        try:
            start_str, end_str = session.time_slot.split('-')
            end_time = timezone.datetime.strptime(end_str.strip(), "%H:%M").time()
            session_end = timezone.datetime.combine(session.date, end_time)
            session_end = timezone.make_aware(session_end)

            # Late grace period (15 minutes after session end)
            late_cutoff = session_end + timedelta(minutes=15)
        except:
            # If time parsing fails, just use QR validity
            session_end = session.qr_validity_end
            late_cutoff = session_end + timedelta(minutes=15)

        # Check if already marked
        already_marked = Attendance.objects.filter(
            session=session,
            student=request.user.student
        ).exists()

        if already_marked:
            messages.warning(request, "You have already marked attendance for this session.")
            return redirect('student_dashboard')

        # Determine attendance status based on time
        if session.qr_validity_start <= now <= session.qr_validity_end:
            status = "Present"
        elif session.qr_validity_end < now <= late_cutoff:
            status = "Late"
        else:
            messages.error(request, "QR code is not valid at this time.")
            return redirect('student_dashboard')

        # Create attendance record
        Attendance.objects.create(
            student=request.user.student,
            session=session,
            course_id=session.course.id,
            timestamp=now,
            attendance_status=status,
            qr_verification_status="Valid",
            ip_address=request.META.get("REMOTE_ADDR")
        )

        messages.success(request, f"Attendance marked as {status} successfully!")
    return redirect('student_dashboard')