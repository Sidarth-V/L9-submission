from django.contrib.auth.models import User
from .models import *
from datetime import datetime, timezone, timedelta
from django.test import RequestFactory, TestCase
from .tasks import *
from .views import GenericTaskView


class QuestionModelTests(TestCase):
    # def test_always_fail(self):
    #     """
    #     This test will always fail ( for now )
    #     """
    #     self.assertIs(True, False)
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")

    def test_authenticated(self):
        """
        Try to GET the tasks listing page, expect the response to redirect to the login page
        """
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/user/login?next=/tasks")

    def test_authenticated(self):
        """
        Try to GET the tasks listing page, expect the response to redirect to the login page
        """
        # Create an instance of a GET request.
        request = self.factory.get("/tasks")
        # Set the user instance on the request.
        request.user = self.user
        # We simply create the view and call it like a regular function
        response = GenericTaskView.as_view()(request)
        # Since we are authenticated we get a 200 response
        self.assertEqual(response.status_code, 200)

class CeleryTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.users = []
        self.users.append(User.objects.create_user(username="sidarth", email="sid@gmail.com", password="sidarth123"))

        Report.objects.filter(user__username="sidarth").update(last_report=datetime.now(timezone.utc).replace(hour = 0) - timedelta(days=1))


    def test_reports(self):
        self.assertEqual(send(), ["Completed Processing User sidarth"])