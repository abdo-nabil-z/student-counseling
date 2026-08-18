from rest_framework.test import APITestCase


class TemplateAPIErrorTests(APITestCase):
    def test_unknown_template_purpose_uses_error_contract(self):
        response = self.client.get(
            "/api/templates/not-a-real-purpose/"
        )

        self.assertEqual(response.status_code, 404)

        error = response.json()["error"]

        self.assertEqual(error["code"], "unknown_template_purpose")
        self.assertIsNone(error["details"])

    
    def test_missing_render_fields_return_validation_error(self):
        response = self.client.post(
            "/api/templates/appointment_invitation/render/",
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        error = response.json()["error"]

        self.assertEqual(error["code"], "validation_error")
        self.assertIn("student_id", error["details"])
        self.assertIn("counselor_id", error["details"])
        self.assertIn("appointment_id", error["details"])
