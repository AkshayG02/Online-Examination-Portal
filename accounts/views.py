from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import AdminSignupForm, FeedbackForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages  

from django.core.paginator import Paginator
from exam.models import Exam, TeacherProfile

# Create your views here.

def home(request):
    exams = Exam.objects.order_by('-date', '-id')  # fallback by id if date same
    paginator = Paginator(exams, 3)  # 3 exams per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'accounts/home.html', {'page_obj': page_obj})

def signup_admin(request):
    if request.method == 'POST':
        form = AdminSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Admin account created successfully. Please log in.')
            return redirect('login')
    else:
        form = AdminSignupForm()
    return render(request, 'accounts/signup_admin.html', {'form': form})



def signup_teacher(request):
    if request.method == 'POST':
        form = TeacherSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher account created successfully. Please log in.')
            return redirect('login')
    else:
        form = TeacherSignupForm()
    return render(request, 'accounts/signup_teacher.html', {'form': form})

# from django.db import transaction
# # def signup_teacher(request):
#     if request.method == 'POST':
#         form = TeacherSignupForm(request.POST)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     user = form.save()

#                     # Explicit TeacherProfile creation
#                     profile = TeacherProfile.objects.create(
#                         user=user,
#                         full_name=user.username,  # Ensure valid data
#                         email=user.email
#                     )

#                     print(f"TeacherProfile created for {user.username}")

#                 messages.success(request, 'Teacher account created successfully. Please log in.')
#                 return redirect('login')

#             except Exception as e:
#                 print('Error creating TeacherProfile:', e)
#                 messages.error(request, 'Something went wrong. Please try again.')

#     else:
#         form = TeacherSignupForm()

#     return render(request, 'accounts/signup_teacher.html', {'form': form})







def signup_student(request):
    if request.method == 'POST':
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student account created successfully. Please log in.')
            return redirect('login')
    else:
        form = StudentSignupForm()
    return render(request, 'accounts/signup_student.html', {'form': form})



def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please enter both username and password')
            return redirect('login')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')



#to restrict views to User Admins

from django.http import HttpResponseForbidden
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Access Denied: Admins only.")
    return wrapper



# Admin Dashboard and CRUD Views 

from django.shortcuts import get_object_or_404
from .models import User
from .forms import AdminSignupForm, TeacherSignupForm, StudentSignupForm

@admin_required
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')

@admin_required
def user_list(request):
    users = User.objects.exclude(role='admin')
    return render(request, 'accounts/user_list.html', {'users': users})


@admin_required
def user_add(request):
    role = request.GET.get('role')
    if role == 'student':
        form_class = StudentSignupForm
    elif role == 'teacher':
        form_class = TeacherSignupForm
    else:
        return HttpResponseForbidden("Invalid role.")

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = form_class()

    return render(request, 'accounts/user_add.html', {'form': form, 'role': role})

@admin_required
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.role == 'student':
        form_class = StudentSignupForm
    elif user.role == 'teacher':
        form_class = TeacherSignupForm
    else:
        return HttpResponseForbidden("Invalid user type.")

    if request.method == 'POST':
        form = form_class(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = form_class(instance=user)

    return render(request, 'accounts/user_edit.html', {'form': form, 'user': user})


@admin_required
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.role == 'admin':
        return HttpResponseForbidden("Cannot delete admin user.")
    user.delete()
    return redirect('user_list')



#contact 
# def contact_view(request):
#     if request.method == 'POST':
#         form = FeedbackForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Thank you for your feedback!')
#             return redirect('contact')  
#     else:
#         form = FeedbackForm()
#     return render(request, 'accounts/contact.html', {'form': form})

def contact_view(request):
    if request.method=='POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your feedback')
            return redirect('contact')
    else:
        form= FeedbackForm()
    return render(request,'accounts/contact.html',{'form':form})    




