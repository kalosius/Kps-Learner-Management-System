from django.contrib import admin
from .models import User, Student, SchoolClass, Subject, Assessment, GradeEntry, AttendanceRecord, BehaviourIncident, MessageThread, Message, Notification, AcademicYear, Term

# Register your models here.
admin.site.register(User)
admin.site.register(Student)
admin.site.register(SchoolClass)
admin.site.register(Subject)
admin.site.register(Assessment)
admin.site.register(GradeEntry)
admin.site.register(AttendanceRecord)
admin.site.register(BehaviourIncident)
admin.site.register(MessageThread)
admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(AcademicYear)
admin.site.register(Term)
