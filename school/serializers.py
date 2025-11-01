from rest_framework import serializers
from .models import User, Student, SchoolClass, Subject, Assessment, GradeEntry, AttendanceRecord, BehaviourIncident, MessageThread, Message, Notification, AcademicYear, Term

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','first_name','last_name','email','role','phone')

class SchoolClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolClass
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    guardian = UserSerializer(many=True, read_only=True)
    class Meta:
        model = Student
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ('recorded_by',)

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = '__all__'
        read_only_fields = ('created_by',)

class GradeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeEntry
        fields = '__all__'
        read_only_fields = ('recorded_by','recorded_at')

class BehaviourSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviourIncident
        fields = '__all__'

# school/serializers.py
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


# nested serializers for detailed student pages.