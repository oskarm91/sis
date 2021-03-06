from django.contrib.auth import authenticate, logout as auth_logout, login as auth_login
from django.shortcuts import render, redirect

from classes.forms import AuthForm, WzorPodpisuFormularz

from users.models import UserProfile
from classes.models import SubjectScheduleDate, ClassSubject, Lesson, Grade, ClassYear

def schedule(request):
    schedule_id = request.GET.get('id', 0)
    class_year = ClassYear.objects.get(id=request.GET.get('class_year'))

    days = []
    for day, name in SubjectScheduleDate.DAYS:
        subjects = SubjectScheduleDate.objects.filter(day=day, klass=class_year, schedule_id=schedule_id)
        days.append({
            'subjects': subjects,
            'name': name
        })

    return render(request, 'classes/schedule.html', {'days': days})


def grades(request):
    subject = ClassSubject.objects.get(id=request.GET.get('id'))
    student = UserProfile.objects.get(id=request.GET.get('student'))
    lessons = Lesson.objects.filter(schedule__subject=subject).order_by('-date')
    grades = Grade.objects.filter(student=student, lesson__schedule__subject=subject).order_by('-lesson__date')

    s = sum([grade.grade*grade.weight for grade in grades])
    n = sum([grade.weight for grade in grades])

    return render(request, 'classes/grades.html', {
        'subject': subject,
        'student': student,
        'lessons': lessons,
        'grades': grades,
        'avg': s/n if n > 0 else '-'
    })


def student_view(request, id):
    student = UserProfile.objects.get(id=id)

    if not 'class_year' in request.GET:
        class_years = ClassYear.objects.filter(students__id=student.id)
        return render(request, 'classes/student_years.html', {
            'student': student,
            'class_years': class_years,
        })
    else:
        class_year = ClassYear.objects.get(id=request.GET.get('class_year'))
        return render(request, 'classes/student.html', {
            'student': student,
            'class_year': class_year,
        })


def parent_view(request):
    student_id = request.GET.get('student', None)
    user = UserProfile.objects.get(user=request.user)
    if not student_id:
        students = [rel.child for rel in request.user.profile.children_rel.all()]
        user = request.user
        userprofile = UserProfile.objects.get(user=user)
        if request.method == 'POST':
            wzorpodpisuform = WzorPodpisuFormularz(request.POST, request.FILES)
            if wzorpodpisuform.is_valid():
                userprofile.signature_upload = request.FILES['wzorpodpisu']
                userprofile.save()
        else:
            wzorpodpisuform = WzorPodpisuFormularz()
        return render(request, 'classes/parent_index.html', {
            'students': students,
            'wzorpodpisuform': wzorpodpisuform,
            'wzorpodpisu': userprofile.signature_upload
        })
    else:
        return student_view(request, student_id)


def index(request):
    if request.method == 'POST':
        form = AuthForm(data=request.POST)

        if form.is_valid():
            auth_login(request, form.user_cache)
    else:
        form = AuthForm()

    user = request.user
    if user is not None and user.is_authenticated():
        if user.profile.is_parent:
            return parent_view(request)
        elif user.profile.is_student:
            return student_view(request, request.user.profile.id)

    return render(request, 'classes/login.html', {'form': form,})


def logout(request):
    auth_logout(request)
    return index(request)
