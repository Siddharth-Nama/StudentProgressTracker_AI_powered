import time
from django.utils.deprecation import MiddlewareMixin
from datetime import date
from django.utils.timezone import now
from django.contrib.auth.middleware import get_user
from .models import StudentActivity, Student

class PageTimeTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user = get_user(request)

        if not request.user.is_authenticated:
            return None  # Explicit return for clarity

        # Start timing when user accesses the page
        request.session['start_time'] = time.time()
        print(f"Start time set: {request.session['start_time']}")  # Debugging

    def process_response(self, request, response):
        print("Processing response...")  # Debugging
        request.user = get_user(request)

        # Skip tracking for teachers and admins
        if hasattr(request.user, 'teacher') or hasattr(request.user, 'admin'):
            return response

        if not request.user.is_authenticated:
            return response  

        print("User:", request.user)

        # Get the student object
        students = Student.objects.all()
        current_student = Student.objects.filter(user__username=request.user).first()

        if not current_student:
            print("Warning: Student object not found for user:", request.user)
            return response

        start_time = request.session.get('start_time')  # Avoid KeyError
        if start_time:
            elapsed_time = round((time.time() - start_time)*1000, 2)  # Calculate time spent correctly
            print(f"Elapsed time: {elapsed_time} seconds")  # Debugging

            page_name = request.path  # Get the current page URL

            # Fetch or create a record for today's activity
            activity, created = StudentActivity.objects.get_or_create(
                student=current_student, 
                date=date.today()
            )

            # Ensure time_spent is a dictionary
            if not isinstance(activity.time_spent, dict):
                activity.time_spent = {}

            # Update the cumulative time spent on this page
            activity.time_spent[page_name] = activity.time_spent.get(page_name, 0) + elapsed_time
            activity.save()  # Save the updated record

            # Remove start_time from session after processing
            del request.session['start_time']

        return response
