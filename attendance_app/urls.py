from django.urls import path
from .views import auth_views, main_views, attendance_views

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),

    # Dashboard URLs
    path('', main_views.home, name='home'),
    path('admin-dashboard/', main_views.admin_dashboard, name='admin_dashboard'),
    path('teacher-dashboard/', main_views.teacher_dashboard, name='teacher_dashboard'),
    path('student-dashboard/', main_views.student_dashboard, name='student_dashboard'),
    path('help/', main_views.help, name='help'),

    # Session URLs
    path('create-session/', main_views.create_session, name='create_session'),
    path('generate-qr/<int:session_id>/', main_views.generate_qr, name='generate_qr'),
    path('show-qr/<int:session_id>/', main_views.show_qr_page, name='show_qr_page'),

    # Attendance URLs
    path('mark-attendance/<int:session_id>/', attendance_views.mark_attendance, name='mark_attendance'),
    path('attendance-report/<int:session_id>/', attendance_views.attendance_report, name='attendance_report'),
    path('admin-attendance-report/', attendance_views.admin_attendance_report, name='admin_attendance_report'),
    path('admin-attendance-report/<int:session_id>/', attendance_views.admin_attendance_report,
         name='admin_attendance_report_detail'),
    path('student-attendance-summary/', attendance_views.student_attendance_summary, name='student_attendance_summary'),
    path('export-attendance/<int:session_id>/', attendance_views.export_attendance_csv, name='export_attendance'),
]
