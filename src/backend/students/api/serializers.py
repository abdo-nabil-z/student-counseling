from rest_framework import serializers

from students.models import Student


class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["matriculation_number","first_name", "last_name", "email", "course_of_studies", "current_study_semester", "credit_points"]


class StudentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"