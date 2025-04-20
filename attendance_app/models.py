from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')

    def __str__(self):
        return f"{self.username} ({self.user_type})"


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.PositiveSmallIntegerField()
    credit_hours = models.DecimalField(max_digits=3, decimal_places=1)

    def __str__(self):
        return f"{self.course_code} - {self.name}"


class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    designation = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.PositiveSmallIntegerField()
    profile_status = models.CharField(max_length=10, choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
                                      default='Active')

    def __str__(self):
        return self.name


class ClassSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.DateField()
    time_slot = models.CharField(max_length=50)
    room_number = models.CharField(max_length=20)
    dynamic_qr_code = models.CharField(max_length=255, unique=True)
    qr_validity_start = models.DateTimeField()
    qr_validity_end = models.DateTimeField()
    session_status = models.CharField(max_length=10, choices=[('Scheduled', 'Scheduled'), ('Ongoing', 'Ongoing'),
                                                              ('Completed', 'Completed')], default='Scheduled')

    def __str__(self):
        return f"{self.course} - {self.date} - {self.time_slot}"

    def is_valid(self):
        now = timezone.now()
        return self.qr_validity_start <= now <= self.qr_validity_end


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(max_length=10,
                                         choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Late', 'Late')])
    qr_verification_status = models.CharField(max_length=10, choices=[('Valid', 'Valid'), ('Invalid', 'Invalid')])
    device_location = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.session} - {self.attendance_status}"
