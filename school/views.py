from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Student, SchoolClass, Assessment, GradeEntry, AttendanceRecord, BehaviourIncident, Notification, MessageThread, Message
from .serializers import UserSerializer, StudentSerializer, SchoolClassSerializer, AssessmentSerializer, GradeEntrySerializer, AttendanceSerializer, BehaviourSerializer, UserSerializer, NotificationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


from . import serializers

from django.utils import timezone


class DashboardView(APIView):
    """Admin/dashboard aggregated data endpoint.

    Returns counts and a few recent items used by the frontend admin dashboard.
    Only accessible to admins and teachers.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # require authenticated user and either admin/teacher role or superuser
        if not user or not user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if not (getattr(user, 'role', None) in ('admin', 'teacher') or getattr(user, 'is_superuser', False)):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        # totals
        total_students = Student.objects.count()
        total_parents = User.objects.filter(role='parent').count()
        total_teachers = User.objects.filter(role='teacher').count()

        # recent students
        recent_students_qs = Student.objects.select_related('current_class').order_by('-created_at')[:6]
        recent_students = [
            {
                'id': s.id,
                'first_name': s.first_name,
                'last_name': s.last_name,
                'admission_number': s.admission_number,
                    'class': s.current_class.name if s.current_class else None,
                    'created_at': s.created_at.isoformat() if getattr(s, 'created_at', None) is not None else None,
            }
            for s in recent_students_qs
        ]

        # recent incidents
        recent_incidents_qs = BehaviourIncident.objects.select_related('student').order_by('-date')[:6]
        recent_incidents = [
            {
                'id': i.id,
                'student': {'id': i.student.id, 'name': f"{i.student.first_name} {i.student.last_name}"} if i.student else None,
                'date': i.date.isoformat() if getattr(i, 'date', None) is not None else None,
                'severity': i.severity,
                'description': (i.description[:140] + '...') if i.description and len(i.description) > 140 else i.description,
            }
            for i in recent_incidents_qs
        ]

        # today's attendance summary
        today = timezone.now().date()
        attendance_today = AttendanceRecord.objects.filter(date=today).count()

        data = {
            'total_students': total_students,
            'total_parents': total_parents,
            'total_teachers': total_teachers,
            'attendance_today': attendance_today,
            'recent_students': recent_students,
            'recent_incidents': recent_incidents,
        }

        return Response(data)

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'


class IsGuardianOrStaff(permissions.BasePermission):
    """Object-level permission: allow access if user is admin/teacher, or is a guardian of the student.

    This prevents parents from accessing other students' records even if they try to call detail endpoints directly.
    """
    def has_object_permission(self, request, view, obj):
        # allow admins and teachers full access
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'role', None) in ('admin', 'teacher') or user.is_superuser:
            return True

        # for student-scoped objects, check guardian relationship
        # obj may be a Student, GradeEntry, AttendanceRecord, BehaviourIncident
        # normalize to a Student instance
        student = None
        if isinstance(obj, Student):
            student = obj
        else:
            # many related models reference student under attribute 'student'
            student = getattr(obj, 'student', None)

        if student is None:
            # if we cannot determine student, deny access by default
            return False

        return user in student.guardian.all()

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.select_related('current_class').prefetch_related('guardian').all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsGuardianOrStaff]

    def get_queryset(self):
        """Return queryset filtered by role: parents only see their guardianed students.

        Admins and teachers see the full set (same dashboard). Parents only see
        students where they are listed as a guardian.
        """
        user = getattr(self.request, 'user', None)
        qs = super().get_queryset()
        if user and user.is_authenticated and getattr(user, 'role', None) == 'parent':
            return qs.filter(guardian=user)
        return qs

    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        student = self.get_object()
        qs = student.attendance.all().order_by('-date')[:100]
        serializer = AttendanceSerializer(qs, many=True)
        return Response(serializer.data)

class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class GradeEntryViewSet(viewsets.ModelViewSet):
    queryset = GradeEntry.objects.select_related('student','assessment').all()
    serializer_class = GradeEntrySerializer
    permission_classes = [IsAuthenticated, IsGuardianOrStaff]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        qs = super().get_queryset()
        # parents see only grade entries for their children
        if user and user.is_authenticated and getattr(user, 'role', None) == 'parent':
            return qs.filter(student__guardian=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsGuardianOrStaff]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        qs = super().get_queryset()
        if user and user.is_authenticated and getattr(user, 'role', None) == 'parent':
            return qs.filter(student__guardian=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

class BehaviourViewSet(viewsets.ModelViewSet):
    queryset = BehaviourIncident.objects.all()
    serializer_class = BehaviourSerializer
    permission_classes = [IsAuthenticated, IsGuardianOrStaff]

    def get_queryset(self):
        user = getattr(self.request, 'user', None)
        qs = super().get_queryset()
        if user and user.is_authenticated and getattr(user, 'role', None) == 'parent':
            return qs.filter(student__guardian=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save()
        return Response({'status':'ok'})


# login and registration views
class RegisterView(APIView):
    permission_classes = []  # allow anyone to register

    def post(self, request):
        data = request.data
        if User.objects.filter(username=data.get('username')).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=data.get('username'),
            password=data.get('password'),
            email=data.get('email', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=data.get('role', 'parent'),  # default to parent
            phone=data.get('phone', '')
        )
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = []  # public

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })



class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
