
import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic

from .models import (
    Course,
    Enrollment,
    Question,
    Choice,
    Submission,
)

logger = logging.getLogger(__name__)


# User registration
def registration_request(request):
    context = {}

    if request.method == "GET":
        return render(
            request,
            "onlinecourse/user_registration_bootstrap.html",
            context,
        )

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["psw"]
        first_name = request.POST["firstname"]
        last_name = request.POST["lastname"]

        if User.objects.filter(username=username).exists():
            context["message"] = "User already exists."
            return render(
                request,
                "onlinecourse/user_registration_bootstrap.html",
                context,
            )

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )

        login(request, user)
        return redirect("onlinecourse:index")

    return redirect("onlinecourse:index")


# User login
def login_request(request):
    context = {}

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("psw", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("onlinecourse:index")

        context["message"] = "Invalid username or password."
        return render(
            request,
            "onlinecourse/user_login_bootstrap.html",
            context,
        )

    return render(
        request,
        "onlinecourse/user_login_bootstrap.html",
        context,
    )


# User logout
def logout_request(request):
    logout(request)
    return redirect("onlinecourse:index")


# Check whether a user is enrolled in a course
def check_if_enrolled(user, course):
    if not user.is_authenticated:
        return False

    return Enrollment.objects.filter(
        user=user,
        course=course,
    ).exists()


# Course list
class CourseListView(generic.ListView):
    template_name = "onlinecourse/course_list_bootstrap.html"
    context_object_name = "course_list"

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by("-total_enrollment")[:10]

        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)

        return courses


# Course details
class CourseDetailView(generic.DetailView):
    model = Course
    template_name = "onlinecourse/course_details_bootstrap.html"


# Enroll in a course
@login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={"mode": "honor"},
    )

    if created:
        course.total_enrollment += 1
        course.save(update_fields=["total_enrollment"])

    return HttpResponseRedirect(
        reverse(
            viewname="onlinecourse:course_details",
            args=(course.id,),
        )
    )


# Extract selected choice IDs from the exam form
def extract_answers(request):
    submitted_answers = []

    for key in request.POST:
        if key.startswith("choice"):
            value = request.POST.get(key)

            try:
                choice_id = int(value)
            except (TypeError, ValueError):
                continue

            submitted_answers.append(choice_id)

    return submitted_answers


# Submit exam answers
@login_required
def submit(request, course_id):
    if request.method != "POST":
        return HttpResponseRedirect(
            reverse(
                "onlinecourse:course_details",
                args=(course_id,),
            )
        )

    course = get_object_or_404(Course, pk=course_id)

    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course,
    )

    selected_ids = extract_answers(request)

    # Fetch only choices belonging to questions in this course.
    selected_choices = Choice.objects.filter(
        id__in=selected_ids,
        question__course=course,
    ).distinct()

    # Reject invalid IDs rather than silently saving unrelated choices.
    if selected_choices.count() != len(set(selected_ids)):
        return render(
            request,
            "onlinecourse/course_detail_bootstrap.html",
            {
                "course": course,
                "error_message": "One or more selected answers are invalid.",
            },
            status=400,
        )

    # Create the submission and associate selected choices.
    submission = Submission.objects.create(
        enrollment=enrollment,
    )
    submission.choices.set(selected_choices)

    return HttpResponseRedirect(
        reverse(
            "onlinecourse:show_exam_result",
            args=(course.id, submission.id),
        )
    )


# Display exam results
@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)

    # Ensure the submission belongs to this course and current user.
    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        enrollment__course=course,
        enrollment__user=request.user,
    )

    selected_choices = submission.choices.all()
    question_list = Question.objects.filter(
        course=course,
    ).order_by("id")

    total_score = 0

    for question in question_list:
        question.score = question.is_get_score(selected_choices)
        total_score += question.score

    maximum_score = sum(
        question.grade for question in question_list
    )

    passed = maximum_score > 0 and total_score >= maximum_score * 0.5

    context = {
        "course": course,
        "submission": submission,
        "question_list": question_list,
        "total_score": total_score,
        "maximum_score": maximum_score,
        "passed": passed,
    }

    return render(
        request,
        "onlinecourse/exam_result_bootstrap.html",
        context,
    )
