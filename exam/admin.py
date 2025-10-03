from django.contrib import admin
from exam.models import Exam,Question,StudentExamAttempt,StudentAnswer,StudentProfile,TeacherProfile

# Register your models here.

admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(StudentExamAttempt)
admin.site.register(StudentAnswer)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
