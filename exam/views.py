from django.shortcuts import render, redirect, get_object_or_404
from .models import Exam, StudentAnswer, StudentExamAttempt, StudentProfile, TeacherProfile
from .forms import ExamForm, StudentProfileForm, TeacherProfileForm
from accounts.views import admin_required  # import your decorator
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test,login_required


# Create your views here.

# helpers for role check
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

def is_admin_or_teacher(user):
    return is_admin(user) or is_teacher(user)


@user_passes_test(is_admin_or_teacher)
def exam_list(request):
    if request.user.role == 'teacher':
        exams = Exam.objects.filter(created_by=request.user)
    else:
        exams = Exam.objects.all()
    return render(request, 'exam/exam_list.html', {'exams': exams})

@user_passes_test(is_admin_or_teacher)
def add_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            return redirect('exam_list')
    else:
        form = ExamForm()
    return render(request, 'exam/add_exam.html', {'form': form})



@user_passes_test(is_admin_or_teacher)
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # ✅ Teacher can edit only own exams
    if request.user.role == 'teacher' and exam.created_by != request.user:
        return redirect('exam_list')

    form = ExamForm(request.POST or None, instance=exam)
    if form.is_valid():
        form.save()
        return redirect('exam_list')
    return render(request, 'exam/edit_exam.html', {'form': form, 'exam': exam})



@user_passes_test(is_admin_or_teacher)
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # ✅ Teacher can delete only own exams
    if request.user.role == 'teacher' and exam.created_by != request.user:
        return redirect('exam_list')

    exam.delete()
    return redirect('exam_list')



# add question 
from .models import Exam, Question
from .forms import QuestionForm
from accounts.views import admin_required


# Exam question dashboard
@user_passes_test(is_admin_or_teacher)
def exam_question_dashboard_view(request):
    exams = Exam.objects.all()
    return render(request, 'exam/exam_question_dashboard.html', {'exams': exams})



@user_passes_test(is_teacher)
def teacher_exam_dashboard(request):
    exams = Exam.objects.filter(created_by=request.user)
    return render(request, 'exam/teacher_exam_dashboard.html', {'exams': exams})









@user_passes_test(is_admin_or_teacher)
def question_list(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # Teacher can only view own exam's questions
    if request.user.role == 'teacher' and exam.created_by != request.user:
        return redirect('exam_list')

    questions = exam.questions.all()
    return render(request, 'exam/question_list.html', {'exam': exam, 'questions': questions})


@user_passes_test(is_admin_or_teacher)
def add_question(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.role == 'teacher' and exam.created_by != request.user:
        return redirect('exam_list')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            return redirect('question_list', exam_id=exam.id)
    else:
        form = QuestionForm()
    return render(request, 'exam/add_question.html', {'form': form, 'exam': exam})

@user_passes_test(is_admin_or_teacher)
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.user.role == 'teacher' and question.exam.created_by != request.user:
        return redirect('exam_list')

    form = QuestionForm(request.POST or None, instance=question)
    if form.is_valid():
        form.save()
        return redirect('question_list', exam_id=question.exam.id)
    return render(request, 'exam/edit_question.html', {'form': form, 'exam': question.exam})


@user_passes_test(is_admin_or_teacher)
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.user.role == 'teacher' and question.exam.created_by != request.user:
        return redirect('exam_list')

    exam_id = question.exam.id
    question.delete()
    return redirect('question_list', exam_id=exam_id)

# student views


@login_required
def student_exam_list(request):
    exams = Exam.objects.all()  
    return render(request, 'student/student_exam_list.html', {'exams': exams})


@login_required
def attempt_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()  # Assuming related_name='questions' in Question model

    total_marks = sum(question.marks for question in questions)
    

    return render(request, 'exam/attempt_exam.html', {
        'exam': exam,
        'questions': questions,
        'total_marks': total_marks,
        'duration_minutes': exam.duration_minutes,  # Passed for dynamic timer
    })


@login_required
def submit_exam(request, exam_id):
    if request.method == 'POST':
        exam = get_object_or_404(Exam, id=exam_id)
        student = request.user

        attempt = StudentExamAttempt.objects.create(student=student, exam=exam)

        total_correct = 0
        total_questions = exam.questions.count()

        for question in exam.questions.all():
            selected_option = request.POST.get(str(question.id))
            if selected_option:
                selected_option = int(selected_option)
                StudentAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_option=selected_option
                )
                if selected_option == question.correct_option:
                    total_correct += 1

        # Calculate score as percentage
        score = (total_correct / total_questions) * 100 if total_questions > 0 else 0
        attempt.score = score
        attempt.save()

        return redirect('student_exam_result', attempt_id=attempt.id)
    else:
        return redirect('student_exam_list')

#update
@login_required
def student_exam_result(request, attempt_id):
    attempt = get_object_or_404(StudentExamAttempt, id=attempt_id, student=request.user)
    answers = attempt.answers.all()

    # Calculate total marks possible for the exam
    total_marks = sum(question.marks for question in attempt.exam.questions.all())

    # Calculate total marks earned from correct answers
    marks_earned = 0
    for ans in answers:
        if ans.selected_option == ans.question.correct_option:
            marks_earned += ans.question.marks

    # Calculate percentage score (optional, you already have attempt.score)
    rounded_score = int(round(attempt.score))
    progress_width = f"width: {rounded_score}%;"

    return render(request, 'student/student_exam_result.html', {
        'attempt': attempt,
        'answers': answers,
        'total_marks': total_marks,
        'marks_earned': marks_earned,
        'rounded_score': rounded_score,
        'progress_width': progress_width,
    })


@login_required
def student_exam_history(request):
    attempts = StudentExamAttempt.objects.filter(student=request.user).order_by('-submitted_at')
    return render(request, 'student/student_exam_history.html', {'attempts': attempts})

@login_required
def delete_student_exam_attempt(request, attempt_id):
    attempt = get_object_or_404(StudentExamAttempt, id=attempt_id, student=request.user)
    
    if request.method == 'POST':
        attempt.delete()
        messages.success(request, "Exam attempt deleted successfully.")
        return redirect('student_exam_history')
    
    # Optional: Render confirmation page if you want
    return render(request, 'student/confirm_delete_attempt.html', {'attempt': attempt})



@login_required
def student_profile(request):
    student = request.user
    attempts = StudentExamAttempt.objects.filter(student=student)
    total_attempts = attempts.count()
    
    if total_attempts > 0:
        average_score = sum(a.score for a in attempts) / total_attempts
    else:
        average_score = 0

    return render(request, 'student/student_profile.html', {
        'student': student,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'average_score': round(average_score, 2),
    })

@login_required
def edit_student_profile(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'student/edit_profile.html', {'form': form})



# student dashboard
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')  # Optional: restrict access

    #return render(request, 'exam/student_dashboard.html')
    return render(request, 'student/student_dashboard.html')

#student instruction
# def exam_instructions_view(request, exam_id):
#     exam = get_object_or_404(Exam, id=exam_id)
#     return render(request, 'student/exam_instructions.html', {'exam': exam})


@login_required
def exam_instructions_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # Get latest attempt of this student for this exam (if exists)
    latest_attempt = StudentExamAttempt.objects.filter(
        student=request.user,
        exam=exam
    ).order_by('-submitted_at').first()

    return render(request, 'student/exam_instructions.html', {
        'exam': exam,
        'latest_attempt': latest_attempt
    })




#teacher dashboard
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from .models import Exam, TeacherProfile


@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('login')

    print('Current User:', request.user)
    profile, created = TeacherProfile.objects.get_or_create(user=request.user)

    if created:
        # If profile was just created, redirect them to edit the profile first
        messages.info(request, 'Please complete your profile before accessing the dashboard.')
        return redirect('edit_teacher_profile')

    exams = Exam.objects.filter(created_by=request.user).annotate(
        submission_count=Count('attempts', distinct=True),
        question_count=Count('questions', distinct=True)
    )

    total_submissions = sum(exam.submission_count for exam in exams)
    total_questions = sum(exam.question_count for exam in exams)

    context = {
        'profile': profile,
        'exams': exams,
        'total_submissions': total_submissions,
        'total_questions': total_questions
    }
    return render(request, 'teacher/teacher_dashboard.html', context)





def teacher_profile(request):
    if request.user.role != 'teacher':
        return redirect('login')

    # Try to get or create the profile
    profile, created = TeacherProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('teacher_profile')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'teacher/teacher_profile.html', {'form': form})

@login_required
def teacher_profile_detail(request):
    if request.user.role != 'teacher':
        return redirect('login')

    profile = get_object_or_404(TeacherProfile, user=request.user)
    return render(request, 'teacher/teacher_profile_detail.html', {'profile': profile})


@login_required
def edit_teacher_profile(request):
    if request.user.role != 'teacher':
        return redirect('login')

    profile, created = TeacherProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('teacher_dashboard')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'teacher/edit_profile.html', {'form': form})


from django.contrib.auth import logout

@login_required
def delete_teacher_profile(request):
    if request.user.role != 'teacher':
        return redirect('login')

    profile = get_object_or_404(TeacherProfile, user=request.user)

    if request.method == 'POST':
        user = request.user
        profile.delete()
        user.delete()
        logout(request)
        messages.success(request, 'Your profile and account have been deleted.')
        return redirect('home')  
    return render(request, 'teacher/confirm_delete.html')


#submission
from django.db.models import Q
from datetime import datetime

@login_required
def view_submissions(request, exam_id):
    if request.user.role != 'teacher':
        return redirect('login')

    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    attempts = StudentExamAttempt.objects.filter(exam=exam)

    # Filtering
    score_min = request.GET.get('score_min')
    date_from = request.GET.get('date_from')

    if score_min:
        attempts = attempts.filter(score__gte=score_min)
    if date_from:
        attempts = attempts.filter(submitted_at__date__gte=date_from)


    return render(request, 'teacher/view_submissions.html', {
        'exam': exam,
        'attempts': attempts,
        'score_min': score_min,
        'date_from': date_from
    })


@login_required
def view_student_answers(request, attempt_id):
    attempt = get_object_or_404(StudentExamAttempt, id=attempt_id)
    if request.user.role != 'teacher' or attempt.exam.created_by != request.user:
        return redirect('login')

    answers = attempt.answers.select_related('question')
    return render(request, 'teacher/view_student_answers.html', {
        'attempt': attempt,
        'answers': answers
    })































