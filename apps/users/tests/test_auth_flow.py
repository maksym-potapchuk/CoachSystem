from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthFlowTests(APITestCase):
    """Smoke test for the register -> login -> me flow."""

    def setUp(self):
        self.register_url = reverse("v1:users:register")
        self.login_url = reverse("v1:users:login")
        self.me_url = reverse("v1:users:me")
        self.password = "Str0ng-Passw0rd!"
        self.email = "employee@example.com"

    def test_register_login_me(self):
        # Register
        res = self.client.post(
            self.register_url,
            {
                "email": self.email,
                "password": self.password,
                "first_name": "Test",
                "last_name": "Employee",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.content)

        # Login -> JWT pair
        res = self.client.post(
            self.login_url,
            {"email": self.email, "password": self.password},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content)
        access = res.data["access"]
        self.assertTrue(access)

        # /users/me/ requires auth
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # With token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content)
        self.assertEqual(res.data["email"], self.email)
        self.assertEqual(res.data["full_name"], "Test Employee")

    def test_register_weak_password_rejected(self):
        res = self.client.post(
            self.register_url,
            {"email": "weak@example.com", "password": "123"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)

