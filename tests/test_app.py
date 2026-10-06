import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Mondays",
            "max_participants": 12,
            "participants": ["member@mergington.edu"],
        },
        "Art Workshop": {
            "description": "Make art",
            "schedule": "Tuesdays",
            "max_participants": 14,
            "participants": ["member@mergington.edu", "art-only@mergington.edu"],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_page(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json()) == {"Chess Club", "Art Workshop"}
    assert response.json()["Chess Club"]["participants"] == ["member@mergington.edu"]


def test_signup_adds_valid_email(client):
    # Arrange
    email = "new-member@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_rejects_duplicate_email(client):
    # Arrange
    email = "member@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "new-member@mergington.edu"

    # Act
    response = client.post("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


@pytest.mark.parametrize(
    "params",
    [{"email": "not-an-email"}, {}],
    ids=["invalid-email", "missing-email"],
)
def test_signup_rejects_invalid_or_missing_email(client, params):
    # Arrange

    # Act
    response = client.post("/activities/Chess Club/signup", params=params)

    # Assert
    assert response.status_code == 422


def test_signup_membership_is_activity_specific(client):
    # Arrange
    email = "art-only@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    activities = client.get("/activities").json()
    assert email in activities["Chess Club"]["participants"]
    assert activities["Art Workshop"]["participants"].count(email) == 1


def test_unregister_removes_participant_only_from_requested_activity(client):
    # Arrange
    email = "member@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    activities = client.get("/activities").json()
    assert email not in activities["Chess Club"]["participants"]
    assert email in activities["Art Workshop"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "member@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_email_not_enrolled(client):
    # Arrange
    email = "not-enrolled@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


@pytest.mark.parametrize(
    "params",
    [{"email": "not-an-email"}, {}],
    ids=["invalid-email", "missing-email"],
)
def test_unregister_rejects_invalid_or_missing_email(client, params):
    # Arrange

    # Act
    response = client.delete("/activities/Chess Club/signup", params=params)

    # Assert
    assert response.status_code == 422