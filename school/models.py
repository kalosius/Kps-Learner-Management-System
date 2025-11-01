from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# --- Custom user with roles ---
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('staff', 'Staff'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def is_teacher(self):
        return self.role == 'teacher'
    def is_parent(self):
        return self.role == 'parent'
    def is_admin(self):
        return self.role == 'admin'

# --- Academic periods ---
class AcademicYear(models.Model):
    name = models.CharField(max_length=50)  # e.g. "2025/2026"
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name

class Term(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=20)  # e.g. Term 1
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.name} {self.academic_year.name}"

# --- Classes/Streams ---
class SchoolClass(models.Model):
    name = models.CharField(max_length=50)  # e.g. "P.4 Blue"
    grade = models.IntegerField()           # numeric grade P1..P7
    teacher_incharge = models.ForeignKey('User', limit_choices_to={'role':'teacher'}, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

# --- Students & Enrollment ---
class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    admission_number = models.CharField(max_length=30, unique=True)
    current_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, related_name='students')
    photo = models.ImageField(upload_to='students/photos/', null=True, blank=True)
    guardian = models.ManyToManyField('User', limit_choices_to={'role':'parent'}, related_name='children')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"

# --- Subjects ---
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name

class ClassSubject(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='class_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('User', limit_choices_to={'role':'teacher'}, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('school_class', 'subject')

# --- Attendance ---
class AttendanceRecord(models.Model):
    ATTENDANCE_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_CHOICES)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendance_records')
    note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'date')

# --- Assessments / Grades ---
class Assessment(models.Model):
    ASSESSMENT_CHOICES = (
        ('exam', 'Exam'),
        ('test', 'Test'),
        ('assignment', 'Assignment'),
        ('continuous', 'Continuous Assessment'),
    )
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    weight = models.FloatField(default=1.0)  # weighting for aggregated score
    assessment_type = models.CharField(max_length=30, choices=ASSESSMENT_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assessments')

    def __str__(self):
        return f"{self.title} - {self.school_class} - {self.subject}"

class GradeEntry(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='grade_entries')
    score = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grade_entries')

    class Meta:
        unique_together = ('student', 'assessment')

# --- Behavior / Discipline ---
class BehaviourIncident(models.Model):
    SEVERITY = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='incidents')
    date = models.DateField(default=timezone.now)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    action_taken = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY, default='low')
    notified_parents = models.BooleanField(default=False)

# --- Messaging between teacher/parent/admin ---
class MessageThread(models.Model):
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)

# --- Notifications (simple) ---
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True, null=True)  # e.g. link to student report

# --- Report snapshot (e.g. term report export) ---
class TermReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='term_reports')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pdf_file = models.FileField(upload_to='reports/', blank=True, null=True)  # optional generated PDF

    class Meta:
        unique_together = ('student', 'term')
