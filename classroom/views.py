from django.shortcuts import render,get_object_or_404,redirect
from django.views import generic
from django.views.generic import  (View,TemplateView,
                                  ListView,DetailView,
                                  CreateView,UpdateView,
                                  DeleteView)
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.
from classroom.forms import UserForm,TeacherProfileForm,StudentProfileForm,MarksForm,MessageForm,NoticeForm,AssignmentForm,SubmitForm,TeacherProfileUpdateForm,StudentProfileUpdateForm
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout,update_session_auth_hash
from django.http import HttpResponseRedirect,HttpResponse
from classroom import models
from classroom.models import *
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.core.mail import send_mail

# For Teacher Sign Up
def TeacherSignUp(request):
    user_type = 'teacher'
    registered = False

    if request.method == "POST":
        user_form = UserForm(data = request.POST)
        teacher_profile_form = TeacherProfileForm(data = request.POST)

        if user_form.is_valid() and teacher_profile_form.is_valid():

            user = user_form.save()
            user.is_teacher = True
            user.save()

            profile = teacher_profile_form.save(commit=False)
            profile.user = user
            profile.save()

            registered = True
        else:
            print(user_form.errors,teacher_profile_form.errors)
    else:
        user_form = UserForm()
        teacher_profile_form = TeacherProfileForm()

    return render(request,'classroom/teacher_signup.html',{'user_form':user_form,'teacher_profile_form':teacher_profile_form,'registered':registered,'user_type':user_type})


###  For Student Sign Up
def StudentSignUp(request):
    user_type = 'student'
    registered = False

    if request.method == "POST":
        user_form = UserForm(data = request.POST)
        student_profile_form = StudentProfileForm(data = request.POST)

        if user_form.is_valid() and student_profile_form.is_valid():

            user = user_form.save()
            user.is_student = True
            user.save()

            profile = student_profile_form.save(commit=False)
            profile.user = user
            profile.save()

            registered = True
        else:
            print(user_form.errors,student_profile_form.errors)
    else:
        user_form = UserForm()
        student_profile_form = StudentProfileForm()

    return render(request,'classroom/student_signup.html',{'user_form':user_form,'student_profile_form':student_profile_form,'registered':registered,'user_type':user_type})

## Sign Up page which will ask whether you are teacher or student.
def SignUp(request):
    return render(request,'classroom/signup.html',{})

## login view.
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username,password=password)

        if user:
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect(reverse('home'))

            else:
                return HttpResponse("Account not active")

        else:
            messages.error(request, "Invalid Details")
            return redirect('classroom:login')
    else:
        return render(request,'classroom/login.html',{})

## logout view.
@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))

## User Profile of student.
class StudentDetailView(LoginRequiredMixin,DetailView):
    context_object_name = "student"
    model = Student
    template_name = 'classroom/student_detail_page.html'

## User Profile for teacher.
class TeacherDetailView(LoginRequiredMixin,DetailView):
    context_object_name = "teacher"
    model = Teacher
    template_name = 'classroom/teacher_detail_page.html'

## Profile update for students.
@login_required
def StudentUpdateView(request,pk):
    profile_updated = False
    student = get_object_or_404(Student,pk=pk)
    if request.method == "POST":
        form = StudentProfileUpdateForm(request.POST,instance=student)
        if form.is_valid():
            profile = form.save(commit=False)
            if 'student_profile_pic' in request.FILES:
                profile.student_profile_pic = request.FILES['student_profile_pic']
            profile.save()
            profile_updated = True
    else:
        form = StudentProfileUpdateForm(request.POST or None,instance=student)
    return render(request,'classroom/student_update_page.html',{'profile_updated':profile_updated,'form':form})

## Profile update for teachers.
@login_required
def TeacherUpdateView(request,pk):
    profile_updated = False
    teacher = get_object_or_404(Teacher,pk=pk)
    if request.method == "POST":
        form = TeacherProfileUpdateForm(request.POST,instance=teacher)
        if form.is_valid():
            profile = form.save(commit=False)
            if 'teacher_profile_pic' in request.FILES:
                profile.teacher_profile_pic = request.FILES['teacher_profile_pic']
            profile.save()
            profile_updated = True
    else:
        form = TeacherProfileUpdateForm(request.POST or None,instance=teacher)
    return render(request,'classroom/teacher_update_page.html',{'profile_updated':profile_updated,'form':form})

## List of all students that teacher has added in their class.
def class_students_list(request):
    query = request.GET.get("q", None)
    students = StudentsInClass.objects.filter(teacher=request.user.Teacher)
    students_list = [x.student for x in students]
    qs = Student.objects.all()
    if query is not None:
        qs = qs.filter(
                Q(name__icontains=query)
                )
    qs_one = []
    for x in qs:
        if x in students_list:
            qs_one.append(x)
        else:
            pass
    context = {
        "class_students_list": qs_one,
    }
    template = "classroom/class_students_list.html"
    return render(request, template, context)

class ClassStudentsListView(LoginRequiredMixin,DetailView):
    model = Teacher
    template_name = "classroom/class_students_list.html"
    context_object_name = "teacher"

## For Marks obtained by the student in all subjects.
class StudentAllMarksList(LoginRequiredMixin,DetailView):
    model = Student
    template_name = "classroom/student_allmarks_list.html"
    context_object_name = "student"

## To give marks to a student.
@login_required
def add_marks(request,pk):
    marks_given = False
    student = get_object_or_404(Student,pk=pk)
    if request.method == "POST":
        form = MarksForm(request.POST)
        if form.is_valid():
            marks = form.save(commit=False)
            marks.student = student
            marks.teacher = request.user.Teacher
            marks.save()
            messages.success(request,'Marks uploaded successfully!')
            return redirect('classroom:submit_list')
    else:
        form = MarksForm()
    return render(request,'classroom/add_marks.html',{'form':form,'student':student,'marks_given':marks_given})

## For updating marks.
@login_required
def update_marks(request,pk):
    marks_updated = False
    obj = get_object_or_404(StudentMarks,pk=pk)
    if request.method == "POST":
        form = MarksForm(request.POST,instance=obj)
        if form.is_valid():
            marks = form.save(commit=False)
            marks.save()
            marks_updated = True
    else:
        form = MarksForm(request.POST or None,instance=obj)
    return render(request,'classroom/update_marks.html',{'form':form,'marks_updated':marks_updated})

## For writing notice which will be sent to all class students.
@login_required
def add_notice(request):
    notice_sent = False
    teacher = request.user.Teacher
    students = StudentsInClass.objects.filter(teacher=teacher)
    students_list = [x.student for x in students]

    if request.method == "POST":
        notice = NoticeForm(request.POST)
        if notice.is_valid():
            object = notice.save(commit=False)
            object.teacher = teacher
            object.save()
            object.students.add(*students_list)
            notice_sent = True
    else:
        notice = NoticeForm()
    return render(request,'classroom/write_notice.html',{'notice':notice,'notice_sent':notice_sent})

## For student writing message to teacher.
@login_required
def write_message(request,pk):
    message_sent = False
    teacher = get_object_or_404(Teacher,pk=pk)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            mssg = form.save(commit=False)
            mssg.teacher = teacher
            mssg.student = request.user.Student
            mssg.save()
            message_sent = True
    else:
        form = MessageForm()
    return render(request,'classroom/write_message.html',{'form':form,'teacher':teacher,'message_sent':message_sent})

## For the list of all the messages teacher have received.
@login_required
def messages_list(request,pk):
    teacher = get_object_or_404(Teacher,pk=pk)
    return render(request,'classroom/messages_list.html',{'teacher':teacher})

## Student can see all notice given by their teacher.
@login_required
def class_notice(request,pk):
    student = get_object_or_404(Student,pk=pk)
    return render(request,'classroom/class_notice_list.html',{'student':student})

## To see the list of all the marks given by the techer to a specific student.
@login_required
def student_marks_list(request,pk):
    error = True
    student = get_object_or_404(Student,pk=pk)
    teacher = request.user.Teacher
    given_marks = StudentMarks.objects.filter(teacher=teacher,student=student)
    return render(request,'classroom/student_marks_list.html',{'student':student,'given_marks':given_marks})

## To add student in the class.
class add_student(LoginRequiredMixin,generic.RedirectView):

    def get_redirect_url(self,*args,**kwargs):
        return reverse('classroom:students_list')

    def get(self,request,*args,**kwargs):
        student = get_object_or_404(Student,pk=self.kwargs.get('pk'))

        try:
            StudentsInClass.objects.create(teacher=self.request.user.Teacher,student=student)
        except:
            messages.warning(self.request,'warning, Student already in class!')
        else:
            messages.success(self.request,'{} successfully added!'.format(student.name))

        return super().get(request,*args,**kwargs)

@login_required
def student_added(request):
    return render(request,'classroom/student_added.html',{})

## List of students which are not added by teacher in their class.
def students_list(request):
    query = request.GET.get("q", None)
    students = StudentsInClass.objects.filter(teacher=request.user.Teacher)
    students_list = [x.student for x in students]
    qs = Student.objects.all()
    if query is not None:
        qs = qs.filter(
                Q(name__icontains=query)
                )
    qs_one = []
    for x in qs:
        if x in students_list:
            pass
        else:
            qs_one.append(x)

    context = {
        "students_list": qs_one,
    }
    template = "classroom/students_list.html"
    return render(request, template, context)

## List of all the teacher present in the portal.
def teachers_list(request):
    query = request.GET.get("q", None)
    qs = Teacher.objects.all()
    if query is not None:
        qs = qs.filter(
                Q(name__icontains=query)
                )

    context = {
        "teachers_list": qs,
    }
    template = "classroom/teachers_list.html"
    return render(request, template, context)


####################################################

## Teacher uploading assignment.
@login_required
def upload_assignment(request):
    assignment_uploaded = False
    teacher = request.user.Teacher
    students = Student.objects.filter(user_student_name__teacher=request.user.Teacher)
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.teacher = teacher
            students = Student.objects.filter(user_student_name__teacher=request.user.Teacher)
            upload.save()
            upload.student.add(*students)
            assignment_uploaded = True
    else:
        form = AssignmentForm()
    return render(request,'classroom/upload_assignment.html',{'form':form,'assignment_uploaded':assignment_uploaded})

## Students getting the list of all the assignments uploaded by their teacher.
@login_required
def class_assignment(request):
    student = request.user.Student
    assignment = SubmitAssignment.objects.filter(student=student)
    assignment_list = [x.submitted_assignment for x in assignment]
    return render(request,'classroom/class_assignment.html',{'student':student,'assignment_list':assignment_list})

## List of all the assignments uploaded by the teacher himself.
@login_required
def assignment_list(request):
    teacher = request.user.Teacher
    return render(request,'classroom/assignment_list.html',{'teacher':teacher})

## For Open the assignments.

@login_required
def open_assignment(request, id=None):
    obj = get_object_or_404(ClassAssignment, id=id)
    
    # Get file extension
    filename = obj.assignment.name
    extension = filename.split('.')[-1].lower()
    
    # Convert to absolute URL
    file_url = request.build_absolute_uri(obj.assignment.url)

    context = {
        "assignment": obj,
        "file_type": extension,
        "file_url": file_url,  # ✅ Pass absolute URL to template
    }
    print('File URL:', file_url)

    # Use a template that can handle different file types
    template = "classroom/view_assignment.html"
    return render(request, template, context)

## For updating the assignments later.
@login_required
def update_assignment(request,id=None):
    obj = get_object_or_404(ClassAssignment, id=id)
    form = AssignmentForm(request.POST or None, instance=obj)
    context = {
        "form": form
    }
    if form.is_valid():
        obj = form.save(commit=False)
        if 'assignment' in request.FILES:
            obj.assignment = request.FILES['assignment']
        obj.save()
        messages.success(request, "Updated Assignment".format(obj.assignment_name))
        return redirect('classroom:assignment_list')
    template = "classroom/update_assignment.html"
    return render(request, template, context)

## For deleting the assignment.
@login_required
def assignment_delete(request, id=None):
    obj = get_object_or_404(ClassAssignment, id=id)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Assignment Removed")
        return redirect('classroom:assignment_list')
    context = {
        "object": obj,
    }
    template = "classroom/assignment_delete.html"
    return render(request, template, context)

## For students submitting their assignment.
@login_required
def submit_assignment(request, id=None):
    student = request.user.Student
    assignment = get_object_or_404(ClassAssignment, id=id)
    teacher = assignment.teacher
    if request.method == 'POST':
        form = SubmitForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.teacher = teacher
            upload.student = student
            upload.submitted_assignment = assignment
            upload.save()
            return redirect('classroom:class_assignment')
    else:
        form = SubmitForm()
    return render(request,'classroom/submit_assignment.html',{'form':form,})

## To see all the submissions done by the students.
@login_required
def submit_list(request):
    teacher = request.user.Teacher
    return render(request,'classroom/submit_list.html',{'teacher':teacher})

##################################################################################################

## For changing password.
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST , user=request.user)

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Password changed")
            return redirect('home')
        else:
            return redirect('classroom:change_password')
    else:
        form = PasswordChangeForm(user=request.user)
        args = {'form':form}
        return render(request,'classroom/change_password.html',args)


def index(request):

	if request.method == 'POST':
		name = request.POST['name']
		email = request.POST['email']
		subject = request.POST['subject']
		message = request.POST['message']

		message = name + " with the email, " + email + ", sent the following message:\n\n" + message

		send_mail(subject,
		 message,
		 'anirudha.17me010@sode-edu.in',
		 ['ab8055shetty@gmail.com'],
		 fail_silently=False)
	return render(request, 'classroom/index.html')



from django.http import JsonResponse
from django.utils.timezone import now
import json

# def log_activity(request):
#     if request.method == "POST":
#         data = json.loads(request.body.decode("utf-8"))
#         student = request.user  # Ensure student is logged in
#         page = data.get("page")
#         time_spent = data.get("timeSpent")

#         # Store in database
#         StudentActivity.objects.create(
#             student=student,
#             page=page,
#             time_spent=time_spent,
#             date=now()
#         )

#         return JsonResponse({"status": "success"})
    

from django.shortcuts import render
from .models import StudentActivity
from django.utils.timezone import datetime

def student_activity_report(request):
    student = request.user
    start_date = request.GET.get("start_date", "2024-01-01")  # Example
    end_date = request.GET.get("end_date", str(datetime.today().date()))

    activities = StudentActivity.objects.filter(
        student=student, date__range=[start_date, end_date]
    )

    return render(request, "activity_report.html", {"activities": activities})


from django.shortcuts import render
from classroom.models import StudentActivity

def teacher_student_activity(request):
    if request.user.is_teacher:
        activities = StudentActivity.objects.all()
        return render(request, "classroom/teacher_student_activity.html", {"activities": activities})
    else:
        return HttpResponse("Unauthorized", status=403)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import StudentActivity
from datetime import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime
from .models import StudentActivity

import google.generativeai as genai
from datetime import datetime
from django.db.models import Q
from django.shortcuts import render
from .models import StudentActivity, Student

# Set your Gemini API Key
genai.configure(api_key="AIzaSyCZlXZ1m18n374GZaZssWPnHnVZWb4D0DY")
models = genai.list_models()

@login_required
def student_progress_dashboard(request):
    query = request.GET.get("q", "").strip()
    date_query = request.GET.get("date", "").strip()

    # Set default values
    if not query:
        query = "2201222CS"
    if not date_query:
        date_query = datetime.now().strftime('%Y-%m-%d')

    # Convert date_query to a date object
    selected_date = datetime.strptime(date_query, "%Y-%m-%d").date()

    # Apply both filters correctly
    students_activities = StudentActivity.objects.filter(
        Q(student__roll_no__icontains=query) & Q(date=selected_date)
    ).order_by('-date')
    
    student = Student.objects.all().filter(roll_no = query).first()
    student_name = ""
    if student:
        student_name = student.name
    print('name -------------',student_name)

    # Create a structured list of student activities
    student_activity_data = []

    for activity in students_activities:
        if hasattr(activity, 'time_spent') and activity.time_spent:
            for page, time in activity.time_spent.items():
                activity_data = {
                "date": activity.date.strftime("%Y-%m-%d"),
                "page": page,  # Using page directly
                "time_spent": time
                }
            student_activity_data.append(activity_data)

    prompt = f"""
    Based on the following student activity data, classify the student's performance as 'Good', 'Average', or 'Poor'. if student is active on total page timing is more than 3600 seconds then average and if stuent timing is greater than 7200 seconds then good and if student timing is less than 3600  seconds then poor.
    Consider factors like time spent on study-related pages (assignments, marks checking) vs. non-productive activities. and time is in seconds not in minutes and give answer in only Good, Average, Poor only not other words.

    Data:
    {student_activity_data}

    Output in only this format:
    {{"performance": "Good" | "Average" | "Poor"}}
    """

    # Initialize Gemini model
    model = genai.GenerativeModel("gemini-1.5-pro")  
    
    # Generate response
    response = model.generate_content(prompt)
    
    # Extract prediction from response
    try:
        # Extract just the performance value from the JSON response
        performance_prediction = response.text.strip('{}"\' ').split(':')[1].strip('"\' ').replace('"}',"")
    except:
        performance_prediction = "Unknown"
    
    return render(request, 'classroom/student_progress_dashboard.html', {
        'students_activities': students_activities,
        'student_name': student_name,
        'performance_prediction': performance_prediction,
    })



@login_required
def teacher_dashboard(request):
    date_query = request.GET.get("date", "").strip()

    if not date_query:
        date_query = datetime.now().strftime('%Y-%m-%d')
    
    print('--------------date_query--------------------',date_query)

    # Convert date_query to a date object
    selected_date = datetime.strptime(date_query, "%Y-%m-%d").date()
 
    print('--------------selected_date--------------------',selected_date)

    # Apply both filters correctly
    today_student_activity = StudentActivity.objects.filter(
        date=selected_date
    ).order_by('-date')
    
    print('--------------today_student_activity--------------------',today_student_activity)
    Rating = {}
    
    for activity in today_student_activity:
        if hasattr(activity, 'time_spent') and activity.time_spent:
            total_time = 0
            for page, time in activity.time_spent.items():
                total_time += time
            if total_time > 7200:
                rating = "Good"
            elif total_time > 3600:
                rating = "Average"
            else:
                rating = "Poor"
            Rating[activity.student.roll_no] = rating  # Assign rating to student's roll_no
    
    print('---------rating------------',Rating)
   
    goodStudent = {}
    averageStudent = {}
    poorStudent = {}
    for rat in Rating:
        if(Rating[rat] == 'Good'):
            goodStudent[rat] = Rating[rat]
        elif(Rating[rat] == 'Average'):
            averageStudent[rat] = Rating[rat]
        else:
            poorStudent[rat] = Rating[rat]

    print('---------goodStudent------------',goodStudent)
    print('---------averageStudent------------',averageStudent)
    print('---------poorStudent------------',poorStudent)
    
    
    goodStudents = list(goodStudent.keys())
    averageStudents = list(averageStudent.keys())
    poorStudents = list(poorStudent.keys())
    print('---------good_students_list------------',goodStudents)
    print('---------average_students_list------------',averageStudents)   
    print('---------poor_students_list------------',poorStudents)

# Determine the maximum length for iteration
    max_lengthe = max(len(goodStudents), len(averageStudents), len(poorStudents))
    print('-------max--------', max_lengthe)
    # Fill missing values with '-'
    goodStudents += ['-'] * (max_lengthe - len(goodStudents))
    averageStudents += ['-'] * (max_lengthe - len(averageStudents))
    poorStudents += ['-'] * (max_lengthe - len(poorStudents))

    student_data = zip(goodStudents, averageStudents, poorStudents)
    return render(request, 'classroom/teacher_dashboard.html', {    
        'today_student_activity': today_student_activity,
        'Rating': Rating,
        "selected_date": selected_date,
        "student_data": student_data,
        "max_length": range(max_lengthe),  # Pass a range for iteration
    })
