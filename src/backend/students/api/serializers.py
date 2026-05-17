from rest_framework import serializers

from students.models import Student

class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["first_name", "last_name", "user_id"]
