from django.db import models
from USER.models import User
from django.utils import timezone

class ClassType(models.Model):
    name = models.CharField(max_length=20, unique=True)  # JUMBA, YOGA, HIIT
    description = models.TextField(blank=True)

DAYS_OF_WEEK = [
    (0, 'Sunday'),
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday'),
]

class Sessions(models.Model):
    class_type = models.ForeignKey(ClassType, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()  
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField()
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'INSTRUCTOR'})

    class Meta:
        unique_together = ('class_type', 'day_of_week', 'start_time')
        
    
    def __str__(self):
        return f"{self.class_type.name} on {self.get_day_of_week_display()} at {self.start_time} to {self.end_time}"

    
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'CLIENT'})
    class_session = models.ForeignKey(Sessions, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'class_session')

