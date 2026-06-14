import os
import random
import time

from locust import HttpUser, between, task


class EduTrackUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        email = os.getenv("LOADTEST_EMAIL")
        password = os.getenv("LOADTEST_PASSWORD")
        role = os.getenv("LOADTEST_ROLE", "Admin")
        if not email or not password:
            raise RuntimeError("LOADTEST_EMAIL and LOADTEST_PASSWORD are required.")
        response = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password, "role": role},
            name="/api/auth/login",
        )
        response.raise_for_status()
        self.headers = {"Authorization": f"Bearer {response.json()['accessToken']}"}

    @task(5)
    def dashboard(self):
        self.client.get("/api/dashboard/analytics", headers=self.headers)

    @task(4)
    def student_search(self):
        self.client.get("/api/admin/students?page=1&perPage=25&search=a", headers=self.headers)

    @task(3)
    def reports(self):
        self.client.get("/api/report-cards?page=1&perPage=25", headers=self.headers)

    @task(3)
    def invoices(self):
        self.client.get("/api/finance/invoices?page=1&perPage=25", headers=self.headers)

    @task(1)
    def register_student(self):
        if os.getenv("ENABLE_WRITE_LOAD_TEST", "false").lower() != "true":
            return
        options = self.client.get("/api/admin/student-form-options", headers=self.headers).json()
        subjects = options.get("subjects", [])
        if not subjects:
            return
        selected = [subject["id"] for subject in subjects[: min(3, len(subjects))]]
        unique = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        self.client.post(
            "/api/admin/students",
            headers=self.headers,
            json={
                "firstName": "Load",
                "lastName": f"Student-{unique}",
                "gradeForm": "Form 1",
                "classStream": "General",
                "classType": "Load Test",
                "numberOfSubjects": len(selected),
                "selectedSubjectIds": selected,
            },
            name="/api/admin/students [write]",
        )
