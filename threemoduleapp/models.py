from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('1', 'Admin'),
        ('2', 'Teacher'),
        ('3', 'Student'),
    )
    user_type = models.CharField(max_length=200, choices=USER_TYPE_CHOICES, default='3')
    status = models.IntegerField(default=0)  # 0: Pending, 1: Approved, 2: Disapproved
    disapproval_reason = models.TextField(blank=True, null=True)  # Reason for disapproval

    class Meta:
        db_table = 'custom_user'

class Course(models.Model):
    course_name = models.CharField(max_length=255)

    def __str__(self):
        return self.course_name

class Teacher(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, related_name='teachers')
    age = models.IntegerField()
    phone_number = models.CharField(max_length=10)
    email = models.EmailField(unique=True)  # Prevent duplicate emails
    image = models.ImageField(upload_to='image/', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name if self.user else self.email}"

class Student(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, related_name='students')
    age = models.IntegerField()
    phone_number = models.CharField(max_length=10)
    email = models.EmailField(unique=True)  # Prevent duplicate emails
    image = models.ImageField(upload_to='image/', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name if self.user else self.email}"