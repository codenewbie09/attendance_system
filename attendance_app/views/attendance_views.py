from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
from ..models import ClassSession, Attendance, Student
from ..decorators import admin_required, teacher_required, student_required
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
    records = Attendance.objects.filter(session=session)

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
