import jwt
import pytest

from app.config import Config

DIRECTOR = {"email": "onlymoney@gmail.com", "password": "evenmoremoney"}

USER = {"forename": "John", "surname": "Doe", "email": "john@gmail.com", "password": "Aa123456"}


def login(client, email, password):
    return client.post("/login", json={"email": email, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("body, message", [
    ({}, "Field forename is missing."),
    ({"forename": " "}, "Field surname is missing."),
    ({"forename": "J", "surname": "D", "email": "", "password": "x"}, "Field email is missing."),
    ({**USER, "email": "john@gmail"}, "Invalid email."),
    ({**USER, "password": "short"}, "Invalid password."),
    ({**USER, "forename": "x" * 300}, "Invalid forename."),
])
def test_register_validation(client, body, message):
    response = client.post("/register", json=body)
    assert response.status_code == 400
    assert response.get_json() == {"message": message}


def test_register_rejects_duplicate_email_case_insensitively(client):
    assert client.post("/register", json=USER).status_code == 200
    response = client.post("/register", json={**USER, "email": "JOHN@gmail.com"})
    assert response.get_json() == {"message": "Email already exists."}


def test_login_returns_token_with_role_claims(client):
    client.post("/register", json=USER)
    response = login(client, USER["email"], USER["password"])

    assert response.status_code == 200
    claims = jwt.decode(response.get_json()["accessToken"], Config.JWT_SECRET_KEY, algorithms=["HS256"])
    assert claims["sub"] == USER["email"]
    assert claims["role"] == "employee"
    assert claims["forename"] == "John"


def test_seeded_director_can_log_in(client):
    token = login(client, DIRECTOR["email"], DIRECTOR["password"]).get_json()["accessToken"]
    claims = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    assert claims["role"] == "director"


def test_login_with_wrong_password(client):
    client.post("/register", json=USER)
    response = login(client, USER["email"], "wrong-password")
    assert response.status_code == 400
    assert response.get_json() == {"message": "Invalid credentials."}


def test_delete_requires_token(client):
    response = client.post("/delete")
    assert response.status_code == 401
    assert response.get_json() == {"msg": "Missing Authorization Header"}


def test_delete_removes_account(client):
    client.post("/register", json=USER)
    token = login(client, USER["email"], USER["password"]).get_json()["accessToken"]

    assert client.post("/delete", headers=bearer(token)).status_code == 200
    assert login(client, USER["email"], USER["password"]).status_code == 400
    assert client.post("/delete", headers=bearer(token)).get_json() == {"message": "Unknown user."}


def test_invalid_token_gets_same_response_as_missing_one(client):
    response = client.post("/delete", headers=bearer("not-a-jwt"))
    assert response.status_code == 401
    assert response.get_json() == {"msg": "Missing Authorization Header"}


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_unknown_route_returns_json_404(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.get_json() == {"message": "Not found."}
