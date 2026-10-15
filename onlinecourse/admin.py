
from django.contrib import admin

from .models import (
    Course,
    Lesson,
    Instructor,
    Learner,
    Question,
    Choice,
    Submission,
)


# Inline lessons inside the Course admin page
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Inline choices inside the Question admin page
class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 2


# Inline questions inside the Course admin page
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 2


# Course admin configuration
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline, QuestionInline]
    list_display = ("name", "pub_date")
    list_filter = ["pub_date"]
    search_fields = ["name", "description"]


# Question admin configuration
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ("question_text", "course", "grade")
    list_filter = ["course"]
    search_fields = ["question_text"]


# Lesson admin configuration
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order"]
    list_filter = ["course"]
    search_fields = ["title"]


# Choice admin configuration
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("choice_text", "question", "is_correct")
    list_filter = ["is_correct"]
    search_fields = ["choice_text"]


# Submission admin configuration
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "enrollment")
    search_fields = ("enrollment__user__username",)


# Register all seven required models
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Submission, SubmissionAdmin)
