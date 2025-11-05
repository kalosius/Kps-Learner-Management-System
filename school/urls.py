from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    StudentViewSet, AssessmentViewSet, GradeEntryViewSet,
    AttendanceViewSet, BehaviourViewSet, RegisterView, LoginView, MeView,
    DashboardView,
    UserViewSet, MessageThreadViewSet,
)

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'users', UserViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'grades', GradeEntryViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'incidents', BehaviourViewSet)
router.register(r'threads', MessageThreadViewSet)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

]

urlpatterns += router.urls
