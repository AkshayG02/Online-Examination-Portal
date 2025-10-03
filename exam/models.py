from django.db import models
from django.conf import settings

# Create your models here.

class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    total_marks = models.IntegerField()
    duration_minutes = models.PositiveIntegerField(default=5)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='exams'
    )

    def __str__(self):
        return self.title


class Question(models.Model):
    exam = models.ForeignKey(
        Exam, 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    question_text = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)

    correct_option = models.IntegerField(choices=[
        (1, 'Option 1'),
        (2, 'Option 2'),
        (3, 'Option 3'),
        (4, 'Option 4')
    ])

    marks = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.question_text



#for Student

from django.contrib.auth.models import User
from django.conf import settings


class StudentExamAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

class StudentAnswer(models.Model):
    attempt = models.ForeignKey(StudentExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.IntegerField(choices=[
        (1, 'Option 1'),
        (2, 'Option 2'),
        (3, 'Option 3'),
        (4, 'Option 4')
    ])

    def __str__(self):
        return f"Answer to {self.question.id} by {self.attempt.student.username}"


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    email=models.EmailField()
    profile_picture = models.ImageField(upload_to='student_profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.full_name
    
# class TeacherProfile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     full_name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=15, blank=True)
#     email = models.EmailField()
#     profile_picture = models.ImageField(upload_to='teacher_profiles/', blank=True, null=True)
#     bio = models.TextField(blank=True)

#     def __str__(self):
#         return self.full_name

class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True,  null=True)
    email = models.EmailField()
    profile_picture = models.ImageField(upload_to='teacher_profiles/', blank=True, null=True)
    bio = models.TextField(blank=True,  null=True)

    def __str__(self):
        return self.full_name
