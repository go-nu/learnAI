from django.db import models

class Employee(models.Model):
    employee_id  = models.CharField(max_length=20, unique=True)
    name         = models.CharField(max_length=50)
    name_en      = models.CharField(max_length=100, blank=True)
    department   = models.CharField(max_length=100)
    role         = models.CharField(max_length=100, blank=True)
    access_level = models.PositiveSmallIntegerField(default=1)
    photo        = models.ImageField(upload_to='employees/', blank=True, null=True)

    def __str__(self):
        return f"{self.employee_id} · {self.name}"


class AccessLog(models.Model):

    class Direction(models.TextChoices):
        IN  = 'IN',  '입장'
        OUT = 'OUT', '퇴장'

    class Status(models.TextChoices):
        GRANTED = 'GRANTED', '허가'
        DENIED  = 'DENIED',  '거부'

    employee         = models.ForeignKey(
                           Employee, on_delete=models.SET_NULL,
                           null=True, blank=True,
                           related_name='access_logs')
    recognized_name  = models.CharField(max_length=100, blank=True)
    timestamp        = models.DateTimeField(auto_now_add=True)
    direction        = models.CharField(max_length=3,  choices=Direction.choices)
    match_confidence = models.FloatField()
    distance         = models.FloatField(default=0.0)
    encoder          = models.CharField(max_length=50, default='dlib_128')
    status           = models.CharField(max_length=10, choices=Status.choices)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        name = self.employee.name if self.employee else 'Unknown'
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} · {name} · {self.status}"
