from rest_framework.test import APITestCase



class AppointmentAPIErrorTests(APITestCase):
    def test_invalid_student_filter_returns_validation_error(self):
        response = self.client.get(
            "/api/appointments/?student=not-an-integer"
        )

        self.assertEqual(response.status_code, 400)
        
        error = response.json()["error"]

        self.assertEqual(error["code"], "validation_error")
        self.assertIn("student", error["details"])