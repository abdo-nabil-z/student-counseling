from django.test import override_settings
from django.urls import path
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.test import APITestCase

from students.models import Student

@api_view(["GET"])
def successful_test_view(request):
    return Response(
        {
            "status": "ok",
        }
    )


@api_view(["POST"])
def validation_error_test_view(request):
    raise ValidationError(
        {
            "name": [
                "This field is required.",
            ],
        }
    )

@api_view(["GET"])
def missing_resource_test_view(request):
    student = get_object_or_404(
        Student,
        pk=999999999,
    )

    return Response(
        {
            "id": student.pk,
        }
    )


@api_view(["GET"])
def unexpected_error_test_view(request):
    raise RuntimeError("Test unexpected exception")


urlpatterns = [
    path("api/test/success/", successful_test_view, name="test-success"),
    path("api/test/validation-error/", validation_error_test_view, name="test-validation-error"),
    path("api/test/unexpected-error/", unexpected_error_test_view, name="test-unexpected-error"),
    path("api/test/missing-resource/",missing_resource_test_view,name="test-missing-resource",
),
]


handler404 = "consultation_backend.error_handlers.api_not_found"
handler500 = "consultation_backend.error_handlers.api_server_error"


@override_settings(
    ROOT_URLCONF=__name__,
    DEBUG=False,
)
class GlobalErrorHandelingTests(APITestCase):
    def test_successful_response_contains_request_id_header(self):
        response = self.client.get("/api/test/success/")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)
    
    def test_validation_error_has_standard_response_shape(self):
        response = self.client.post("/api/test/validation-error/", data={}, format="json")

        self.assertEqual(response.status_code, 400)

        body = response.json()
        error = body["error"]

        self.assertEqual(error["code"], "validation_error")
        self.assertEqual(error["message"], "The submitted data is invalid.")
        self.assertEqual(
            error["details"],
            {
                "name": [
                    "This field is required.",
                ],
            },
        )
        self.assertEqual(error["request_id"], response["X-Request-ID"])

    
    def test_unexpected_error_returns_safe_500_response(self):
        with self.assertLogs("consultation_backend.exceptions", level="ERROR"):
            response = self.client.get("/api/test/unexpected-error/")
        
        self.assertEqual(response.status_code, 500)

        body = response.json()
        error = body["error"]

        self.assertEqual(error["code"], "internal_server_error")
        self.assertEqual(error["message"], "An unexpected server error occurred.")
        self.assertIsNone(error["details"])
        self.assertEqual(error["request_id"], response["X-Request-ID"])
        
        self.assertNotIn("Test unexpected exception", response.content.decode())


    def test_unknown_api_route_returns_json_404(self):
        response = self.client.get("/api/endpoint-that-does-not-exist/")

        self.assertEqual(response.status_code, 404)

        body = response.json()
        error = body["error"]

        self.assertEqual(error["code"], "endpoint_not_found")
        self.assertEqual(error["message"], "The requested API endpoint was not found.")
        self.assertEqual(error["request_id"], response["X-Request-ID"])


    def test_missing_database_resource_has_distinct_404(
        self,
    ):
        response = self.client.get(
            "/api/test/missing-resource/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        error = response.json()["error"]

        self.assertEqual(
            error["code"],
            "resource_not_found",
        )

        self.assertEqual(
            error["message"],
            "The requested resource does not exist.",
        )


class SchemaDocumentationTests(APITestCase):
    def _get_schema(self):
        response = self.client.get(
            "/api/schema/?format=json"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        return response.json()

    def test_swagger_title_is_correct(self):
        schema = self._get_schema()

        self.assertEqual(
            schema["info"]["title"],
            "Consultation Backend APIs",
        )

    def test_create_appointment_documents_overlap_warning(self):
        schema = self._get_schema()

        responses = schema["paths"][
            "/api/appointments/create-appointment/"
        ]["post"]["responses"]

        self.assertIn(
            "409",
            responses,
        )

    def test_update_appointment_documents_overlap_warning(self):
        schema = self._get_schema()

        responses = schema["paths"][
            "/api/appointments/{appointment_id}/"
        ]["patch"]["responses"]

        self.assertIn(
            "409",
            responses,
        )

    def test_slot_creation_does_not_document_overlap_warning(self):
        schema = self._get_schema()

        responses = schema["paths"][
            "/api/counselors/{counselor_id}/slots/"
        ]["post"]["responses"]

        self.assertNotIn(
            "409",
            responses,
        )

    def test_minutes_upload_documents_any_file_type(self):
        schema = self._get_schema()

        operation = schema["paths"][
            "/api/appointments/{appointment_id}/minutes/"
        ]["post"]

        description = (
            operation["requestBody"]
            ["content"]
            ["multipart/form-data"]
            ["schema"]
            ["properties"]
            ["file"]
            ["description"]
        )

        self.assertIn(
            "Any file type",
            description,
        )

    def test_student_appointment_documents_success_response(self):
        schema = self._get_schema()

        responses = schema["paths"][
            "/api/students/{student_id}/appointment/"
        ]["get"]["responses"]

        self.assertIn(
            "200",
            responses,
        )

        self.assertIn(
            "404",
            responses,
        )