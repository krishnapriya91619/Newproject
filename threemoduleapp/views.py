from django.db import models
from django.contrib.auth.models import AbstractUser
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, Teacher, Student, Course
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.hashers import make_password
from django.db.models import Q
import random
import secrets
import string


def home(request):
    return render(request, 'home.html')

def teacher_register(request):
    courses = Course.objects.all()
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        if CustomUser.objects.filter(Q(username=username)).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'teacher_register.html', {'courses': courses})
        if Teacher.objects.filter(Q(email=email)).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'teacher_register.html', {'courses': courses})

        user = CustomUser.objects.create(
            username=username,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=email,
            user_type='2',
            status=0
        )
        Teacher.objects.create(
            user=user,
            age=request.POST['age'],
            phone_number=request.POST['phone_number'],
            email=email,
            image=request.FILES.get('image'),
            course_id=request.POST['course']
        )
        messages.success(request, 'Please wait registration is successful please wait for admin approval')
        return render(request, 'teacher_register.html', {'courses': courses, 'show_modal': True})
    return render(request, 'teacher_register.html', {'courses': courses})

def student_register(request):
    courses = Course.objects.all()
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        if CustomUser.objects.filter(Q(username=username)).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'student_register.html', {'courses': courses})
        if Student.objects.filter(Q(email=email)).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'student_register.html', {'courses': courses})

        user = CustomUser.objects.create(
            username=username,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=email,
            user_type='3',
            status=0
        )
        Student.objects.create(
            user=user,
            age=request.POST['age'],
            phone_number=request.POST['phone_number'],
            email=email,
            image=request.FILES.get('image'),
            course_id=request.POST['course']
        )
        messages.success(request, 'Please wait registration is successful please wait for admin approval')
        return render(request, 'student_register.html', {'courses': courses, 'show_modal': True})
    return render(request, 'student_register.html', {'courses': courses})

@login_required
def admin_dashboard(request):
    if not (request.user.is_superuser or request.user.user_type == '1'):
        return redirect('home')
    pending_teachers = Teacher.objects.filter(user__status=0)
    pending_students = Student.objects.filter(user__status=0)
    return render(request, 'admin_dashboard.html', {
        'pending_teachers': pending_teachers,
        'pending_students': pending_students,
        'pending_count': pending_teachers.count() + pending_students.count()
    })

@login_required
def approve_user(request, user_id):
    if not (request.user.is_superuser or request.user.user_type == '1'):
        return redirect('home')
    try:
        user = CustomUser.objects.get(id=user_id)
        related_model = Teacher if user.user_type == '2' else Student if user.user_type == '3' else None
        related_instance = related_model.objects.get(user=user) if related_model else None
    except Exception as e:
        messages.error(request, 'User not found.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        if 'approve' in request.POST:
            password = str(random.randint(100000, 999999))  # 6-digit numeric password
            user.password = make_password(password)
            user.status = 1
            user.save()
            try:
                send_mail(
                    'Account Approved',
                    f'Hello {user.first_name},\n\nYour account has been approved.\n\n'
                    f'Username: {user.username}\nPassword: {password}\n\n'
                    f'Login here: {request.build_absolute_uri("/login/")}\n\n'
                    f'Regards,\nTuition Centre Admin',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'User approved and email sent.')
            except Exception as e:
                messages.error(request, f'Error sending approval email: {e}')
        elif 'disapprove' in request.POST:
            reason = 'Your application did not meet our requirements.'
            user.status = 2
            user.save()
            try:
                send_mail(
                    'Account Disapproved',
                    f'Hello {user.first_name},\n\nYour account has been disapproved.\n'
                    f'Reason: {reason}\n\nRegards,\nTuition Centre Admin',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                if related_instance:
                    related_instance.delete()
                user.delete()
                messages.success(request, 'User disapproved and deleted. Email sent.')
            except Exception as e:
                messages.error(request, f'Error sending disapproval email: {e}')
        return redirect('admin_dashboard')

    return render(request, 'approve_user.html', {'user': user})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                messages.success(request, 'Logged in as Superuser.')
                return redirect('admin_dashboard')
            if user.status == 1:
                if user.user_type == '1':
                    messages.success(request, 'Logged in as Admin.')
                    return redirect('admin_dashboard')
                elif user.user_type == '2':
                    messages.success(request, 'Logged in as Teacher.')
                    return redirect('teacher_dashboard')
                elif user.user_type == '3':
                    messages.success(request, 'Logged in as Student.')
                    return redirect('student_dashboard')
            else:
                messages.error(request, 'Your account is pending approval or disapproved.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid credentials or user not found.')
            return redirect('login')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')

@login_required
def add_course(request):
    if request.user.user_type != '1':
        return redirect('home')
    if request.method == 'POST':
        course_name = request.POST['course_name']
        Course.objects.create(course_name=course_name)
        messages.success(request, 'Course added successfully!')
        return redirect('add_course')
    return render(request, 'add_course.html')

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = CustomUser.objects.get(email=email)
            if user.status == 1:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_link = request.build_absolute_uri(f'/reset/{uid}/{token}/')
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Password reset link sent to your email.')
            else:
                messages.error(request, 'Your account is not approved.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Email not found.')
        return redirect('password_reset_request')
    return render(request, 'password_reset_request.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
            elif len(password) < 8 or not any(c.isdigit() for c in password) or \
                 not any(c.isalpha() for c in password) or \
                 not any(c in string.punctuation for c in password):
                messages.error(request, 'Password must be at least 8 characters long and contain letters, numbers, and special characters.')
            else:
                user.password = make_password(password)
                user.save()
                messages.success(request, 'Password reset successfully. You can now log in.')
                return redirect('login')
        return render(request, 'password_reset_confirm.html')
    else:
        messages.error(request, 'Invalid reset link.')
        return redirect('password_reset_request')



from django.core.mail import send_mail
from django.conf import settings

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8 or not any(c.isdigit() for c in new_password) or \
             not any(c.isalpha() for c in new_password) or \
             not any(c in string.punctuation for c in new_password):
            messages.error(request, 'Password must be at least 8 characters, with letters, numbers, and special characters.')
        else:
            # Save the password temporarily before hashing
            raw_password = new_password

            request.user.set_password(raw_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in

            # Send username and raw password in email
            try:
                send_mail(
                    'Your Password Has Been Changed',
                    f"Hello {request.user.first_name},\n\n"
                    f"Your password was successfully changed.\n\n"
                    f"Username: {request.user.username}\n"
                    f"New Password: {raw_password}\n\n"
                    f"If you did not make this change, please contact support immediately.\n\n"
                    f"Regards,\nTuition Centre Admin",
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.error(request, f"Password changed, but failed to send email: {e}")

            messages.success(request, 'Password changed successfully.')

            # Redirect to appropriate dashboard
            if request.user.user_type == '2':
                return redirect('teacher_dashboard')
            elif request.user.user_type == '3':
                return redirect('student_dashboard')
            elif request.user.user_type == '1' or request.user.is_superuser:
                return redirect('admin_dashboard')

    return render(request, 'change_password.html')



@login_required
def teacher_dashboard(request):
    if request.user.user_type != '2':
        return redirect('home')
    teacher = Teacher.objects.get(user=request.user)
    return render(request, 'teacher_dashboard.html', {'user': request.user, 'teacher': teacher})

@login_required
def student_dashboard(request):
    if request.user.user_type != '3':
        return redirect('home')
    student = Student.objects.get(user=request.user)
    return render(request, 'student_dashboard.html', {'user': request.user, 'student': student})
