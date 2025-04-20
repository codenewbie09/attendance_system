from django.contrib import admin
from .models import (
    CustomUser, Department, Course, Teacher,
    Student, ClassSession, Attendance
)

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active')
    search_fields = ('username', 'email')

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_code', 'department', 'semester', 'credit_hours')
    list_filter = ('department', 'semester')
    search_fields = ('name', 'course_code')

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'department', 'designation')
    list_filter = ('department', 'designation')
    search_fields = ('name', 'email')

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_no', 'department', 'semester', 'profile_status')
    list_filter = ('department', 'semester', 'profile_status')
    search_fields = ('name', 'roll_no', 'email')

class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'teacher', 'date', 'time_slot', 'session_status')
    list_filter = ('course', 'teacher', 'date', 'session_status')
    search_fields = ('course__name', 'teacher__name')

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'timestamp', 'attendance_status', 'qr_verification_status')
    list_filter = ('attendance_status', 'qr_verification_status', 'session')
    search_fields = ('student__name', 'student__roll_no')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(ClassSession, ClassSessionAdmin)
admin.site.register(Attendance, AttendanceAdmin)
