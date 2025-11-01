from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    StudentViewSet, AssessmentViewSet, GradeEntryViewSet,
    AttendanceViewSet, BehaviourViewSet, RegisterView, LoginView, MeView
)

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'grades', GradeEntryViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'incidents', BehaviourViewSet)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', MeView.as_view(), name='me'),

]

urlpatterns += router.urls
