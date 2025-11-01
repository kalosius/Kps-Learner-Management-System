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





from school import serializers

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.select_related('current_class').prefetch_related('guardian').all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)

class BehaviourViewSet(viewsets.ModelViewSet):
    queryset = BehaviourIncident.objects.all()
    serializer_class = BehaviourSerializer
    permission_classes = [IsAuthenticated]

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
