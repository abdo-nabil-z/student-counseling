from rest_framework import serializers
from students.models import Student
from documents.api.serializers import DocumentInfoSerializer


class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "matriculation_number",
            "first_name",
            "last_name",
            "email",
            "course_of_studies",
            "current_study_semester",
            "credit_points",
        ]


class StudentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "matriculation_number",
            "first_name",
            "last_name",
            "email",
            "course_of_studies",
            "current_study_semester",
            "credit_points",
            "contact_status",
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    initial_study_plan = DocumentInfoSerializer(read_only=True)
    final_study_plan = DocumentInfoSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "matriculation_number",
            "first_name",
            "last_name",
            "email",
            "course_of_studies",
            "current_study_semester",
            "credit_points",
            "contact_status",
            "initial_study_plan",
            "final_study_plan",
            "created_at",
            "updated_at",
        ]