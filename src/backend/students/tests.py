from rest_framework.test import APITestCase



class StudentAPIErrorTests(APITestCase):
    def test_invalid_semester_cleanup_confirmation_uses_error_contract(self):
        response = self.client.delete(
            "/api/students/semester-cleanup/",
            data={
                "confirm": "wrong-value",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        error = response.json()["error"]

        self.assertEqual(error["code"], "validation_error")
        self.assertIn("confirm", error["details"])
        self.assertEqual(error["request_id"], response["X-Request-ID"])