"""Tests for the High School Management System API"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before and after each test"""
    original_activities = deepcopy(activities)
    yield
    # Reset activities after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        # Arrange
        # No setup needed, activities are pre-populated

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Test that activities include all required fields"""
        # Arrange
        # No setup needed, activities fixture provides test data

        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]

        # Assert
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that activities include participant list"""
        # Arrange
        # No setup needed, Chess Club is pre-populated with participants

        # Act
        response = client.get("/activities")
        data = response.json()
        chess = data["Chess Club"]

        # Assert
        assert isinstance(chess["participants"], list)
        assert "michael@mergington.edu" in chess["participants"]


class TestSignUpForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signing up adds a participant to the activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert email in activities[activity_name]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signing up for a non-existent activity returns 404"""
        # Arrange
        activity_name = "Fake Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_participant_returns_400(self, client, reset_activities):
        """Test that signing up the same participant twice returns 400"""
        # Arrange
        activity_name = "Chess Club"
        email = "duplicate@mergington.edu"

        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Act - Second signup attempt
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student already signed up for this activity"

    def test_signup_prevents_duplicate_registrations(self, client, reset_activities):
        """Test that participant is only added once to the list"""
        # Arrange
        activity_name = "Chess Club"
        email = "unique@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        count = activities[activity_name]["participants"].count(email)
        assert count == 1

    def test_signup_with_existing_participant(self, client, reset_activities):
        """Test that existing participants cannot sign up again"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregistering removes a participant from the activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that unregistering from non-existent activity returns 404"""
        # Arrange
        activity_name = "Fake Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_nonparticipant_returns_404(self, client, reset_activities):
        """Test that unregistering a non-participant returns 404"""
        # Arrange
        activity_name = "Chess Club"
        email = "notasignup@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_and_signup_again(self, client, reset_activities):
        """Test that a participant can unregister and sign up again"""
        # Arrange
        email = "temp@mergington.edu"
        activity = "Chess Club"

        # Act - Sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Assert - Verify signup
        assert email in activities[activity]["participants"]

        # Act - Unregister
        client.delete(f"/activities/{activity}/signup?email={email}")

        # Assert - Verify unregister
        assert email not in activities[activity]["participants"]

        # Act - Sign up again
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert - Verify second signup
        assert response.status_code == 200
        assert email in activities[activity]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""

    def test_multiple_participants_signup(self, client, reset_activities):
        """Test multiple different participants can sign up"""
        # Arrange
        activity = "Programming Class"
        emails = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu",
        ]
        initial_count = len(activities[activity]["participants"])

        # Act
        responses = []
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            responses.append(response)

        # Assert
        assert all(r.status_code == 200 for r in responses)
        assert len(activities[activity]["participants"]) == initial_count + len(emails)
        assert all(email in activities[activity]["participants"] for email in emails)

    def test_participant_signup_and_unregister_multiple_activities(
        self, client, reset_activities
    ):
        """Test that a participant can sign up and unregister from multiple activities"""
        # Arrange
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Studio"]

        # Act - Sign up for multiple activities
        signup_responses = []
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            signup_responses.append(response)

        # Assert - Verify all signups successful
        assert all(r.status_code == 200 for r in signup_responses)
        for activity in activities_to_join:
            assert email in activities[activity]["participants"]

        # Act - Unregister from one activity
        client.delete(f"/activities/Chess Club/signup?email={email}")

        # Assert - Verify unregister from one and still in others
        assert email not in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]
        assert email in activities["Art Studio"]["participants"]
