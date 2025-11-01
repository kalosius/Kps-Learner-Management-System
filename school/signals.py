# signals to auto-notify parents when grades/behaviour are added:
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import GradeEntry, BehaviourIncident, Notification

@receiver(post_save, sender=GradeEntry)
def grade_entry_notify(sender, instance, created, **kwargs):
    if created:
        student = instance.student
        # notify all guardians
        for parent in student.guardian.all():
            Notification.objects.create(
                user=parent,
                title=f"New grade for {student.first_name}",
                message=f"{instance.assessment.title} - {instance.score}. Remarks: {instance.remarks}",
                link=f"/students/{student.id}/reports/{instance.assessment.id}"
            )

@receiver(post_save, sender=BehaviourIncident)
def behaviour_notify(sender, instance, created, **kwargs):
    if created:
        student = instance.student
        for parent in student.guardian.all():
            Notification.objects.create(
                user=parent,
                title=f"Behaviour incident for {student.first_name}",
                message=instance.description,
                link=f"/students/{student.id}/incidents/{instance.id}"
            )

