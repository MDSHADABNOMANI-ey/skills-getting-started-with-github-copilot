"""
Comprehensive integration tests for the Mergington High School Activities API.

Tests cover all endpoints with happy paths, error cases, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient with fresh app state."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test."""
    # Store initial state
    initial_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and games",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis skills development and friendly matches",
            "schedule": "Wednesdays and Saturdays, 3:00 PM - 4:30 PM",
            "max_participants": 16,
            "participants": ["sarah@mergington.edu", "lucas@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and visual arts creation",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["grace@mergington.edu"]
        },
        "Music Band": {
            "description": "Learn instruments and perform in school concerts",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["alex@mergington.edu", "nina@mergington.edu"]
        },
        "Debate Club": {
            "description": "Develop public speaking and critical thinking skills",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 14,
            "participants": ["marcus@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Compete in science competitions and experiments",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["isabella@mergington.edu", "ethan@mergington.edu"]
        }
    }
    
    # Clear and repopulate activities
    activities.clear()
    activities.update(initial_activities)
    yield
    # Cleanup after test
    activities.clear()
    activities.update(initial_activities)


# ============================================================================
# Tests for GET /
# ============================================================================

class TestRoot:
    """Test the root endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Root path should redirect to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ============================================================================
# Tests for GET /activities
# ============================================================================

class TestGetActivities:
    """Test the get activities endpoint."""

    def test_get_all_activities(self, client):
        """Should return all activities with correct structure."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # All 9 activities
        
        # Verify structure of one activity
        assert "Chess Club" in data
        chess = data["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess
        assert isinstance(chess["participants"], list)

    def test_all_activities_have_required_fields(self, client):
        """All activities should have required fields."""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        for activity_name, activity_data in data.items():
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity '{activity_name}' missing required fields"

    def test_participants_are_email_list(self, client):
        """Participants should be a list of email strings."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            participants = activity_data["participants"]
            assert isinstance(participants, list), \
                f"Participants in '{activity_name}' should be a list"
            for participant in participants:
                assert isinstance(participant, str), \
                    f"Participant in '{activity_name}' should be string (email)"
                assert "@" in participant, \
                    f"Participant in '{activity_name}' should be valid email format"


# ============================================================================
# Tests for POST /activities/{activity_name}/signup
# ============================================================================

class TestSignup:
    """Test the signup endpoint."""

    def test_successful_signup(self, client):
        """Student should successfully sign up for an activity."""
        response = client.post(
            "/activities/Art%20Studio/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Art Studio" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Art Studio"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Signup should return 404 if activity doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email(self, client):
        """Signup should return 400 if student already signed up."""
        # Try to signup someone already registered
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_activities_same_email(self, client):
        """Same email should be able to signup for multiple activities."""
        email = "testuser@mergington.edu"
        
        # Signup for first activity
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Signup for second activity
        response2 = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]

    def test_signup_special_characters_in_email(self, client):
        """Should handle emails with special characters."""
        email = "student+lab@mergington.edu"
        response = client.post(
            "/activities/Art%20Studio/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Art Studio"]["participants"]


# ============================================================================
# Tests for DELETE /activities/{activity_name}/unregister
# ============================================================================

class TestUnregister:
    """Test the unregister endpoint."""

    def test_successful_unregister(self, client):
        """Student should successfully unregister from an activity."""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Unregister should return 404 if activity doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered(self, client):
        """Unregister should return 400 if student is not registered."""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_from_multiple_activities(self, client):
        """Should be able to unregister from all activities."""
        email = "testuser@mergington.edu"
        
        # First signup for multiple activities
        client.post("/activities/Chess%20Club/signup", params={"email": email})
        client.post("/activities/Art%20Studio/signup", params={"email": email})
        
        # Unregister from first
        response1 = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister from second
        response2 = client.delete(
            "/activities/Art%20Studio/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify not in either
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email not in data["Chess Club"]["participants"]
        assert email not in data["Art Studio"]["participants"]

    def test_unregister_same_person_twice(self, client):
        """Unregistering same person twice should fail on second attempt."""
        email = "testuser@mergington.edu"
        
        # Signup first
        client.post("/activities/Chess%20Club/signup", params={"email": email})
        
        # First unregister
        response1 = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400


# ============================================================================
# Integration and Complex Scenarios
# ============================================================================

class TestIntegrationScenarios:
    """Test complex real-world scenarios."""

    def test_signup_and_unregister_cycle(self, client):
        """Complete cycle: signup, verify, unregister, verify."""
        email = "cycle@mergington.edu"
        activity = "Art%20Studio"
        
        # Initial state: not registered
        response = client.get("/activities")
        assert email not in response.json()["Art Studio"]["participants"]
        
        # Signup
        signup_response = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert signup_response.status_code == 200
        
        # Verify registered
        response = client.get("/activities")
        assert email in response.json()["Art Studio"]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister", params={"email": email})
        assert unregister_response.status_code == 200
        
        # Verify not registered
        response = client.get("/activities")
        assert email not in response.json()["Art Studio"]["participants"]

    def test_multiple_concurrent_signups(self, client):
        """Multiple different students signups should work."""
        emails = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                "/activities/Programming%20Class/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are registered
        activities_response = client.get("/activities")
        data = activities_response.json()
        for email in emails:
            assert email in data["Programming Class"]["participants"]

    def test_activity_with_spaces_in_name(self, client):
        """Activities with spaces should be URL encoded properly."""
        # Programming Class has spaces
        response = client.get("/activities")
        assert "Programming Class" in response.json()
        
        # Signup for activity with spaces
        signup_response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "test@mergington.edu"}
        )
        assert signup_response.status_code == 200

    def test_participant_count_changes_correctly(self, client):
        """Participant count should update on signup/unregister."""
        email = "counter@mergington.edu"
        
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Gym Class"]["participants"])
        
        # Signup
        client.post("/activities/Gym%20Class/signup", params={"email": email})
        response2 = client.get("/activities")
        after_signup_count = len(response2.json()["Gym Class"]["participants"])
        assert after_signup_count == initial_count + 1
        
        # Unregister
        client.delete("/activities/Gym%20Class/unregister", params={"email": email})
        response3 = client.get("/activities")
        after_unregister_count = len(response3.json()["Gym Class"]["participants"])
        assert after_unregister_count == initial_count
