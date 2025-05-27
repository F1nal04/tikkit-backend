import pytest
from fastapi import status


class TestAuthentication:
    """Integration tests for authentication endpoints."""

    def test_user_registration_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "duplicate@test.com",
            "password": "DuplicatePass123!",
            "name": "Duplicate User"
        }
        
        # First registration should succeed
        response1 = client.post("/register", json=user_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second registration with same email should fail
        response2 = client.post("/register", json=user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response2.json()["detail"]

    def test_user_registration_weak_password(self, client, test_user_data):
        """Test registration with weak password fails."""
        weak_password_data = test_user_data.copy()
        weak_password_data["password"] = "weak"
        
        response = client.post("/register", json=weak_password_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Password must be at least 8 characters" in response.json()["detail"]

    def test_user_login_success(self, client):
        """Test successful user login."""
        user_data = {
            "email": "login@test.com",
            "password": "LoginPass123!",
            "name": "Login User"
        }
        
        # First register the user
        client.post("/register", json=user_data)
        
        # Then try to login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/token", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_user_login_wrong_email(self, client):
        """Test login with wrong email fails."""
        user_data = {
            "email": "wrongemail@test.com",
            "password": "WrongEmailPass123!",
            "name": "Wrong Email User"
        }
        
        # Register user
        client.post("/register", json=user_data)
        
        # Try to login with wrong email
        login_data = {
            "username": "notregistered@example.com",
            "password": user_data["password"]
        }
        response = client.post("/token", data=login_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Incorrect email or password" in response.json()["detail"]

    def test_user_login_wrong_password(self, client):
        """Test login with wrong password fails."""
        user_data = {
            "email": "wrongpass@test.com",
            "password": "WrongPassPass123!",
            "name": "Wrong Pass User"
        }
        
        # Register user
        client.post("/register", json=user_data)
        
        # Try to login with wrong password
        login_data = {
            "username": user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/token", data=login_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Incorrect email or password" in response.json()["detail"]

    def test_protected_endpoint_without_token(self, client, test_ticket_data):
        """Test accessing protected endpoint without token fails."""
        response = client.post("/ticket", json=test_ticket_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_invalid_token(self, client, test_ticket_data):
        """Test accessing protected endpoint with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/ticket", json=test_ticket_data, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_valid_token(self, client, authenticated_user, test_ticket_data):
        """Test accessing protected endpoint with valid token succeeds."""
        response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        assert response.status_code == status.HTTP_200_OK

    def test_registration_returns_working_token(self, client):
        """Test that token from registration can be used immediately."""
        user_data = {
            "email": "tokentest@test.com",
            "password": "TokenTestPass123!",
            "name": "Token Test User"
        }
        
        # Register user
        register_response = client.post("/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Use token to access protected endpoint
        user_response = client.get("/user", headers=headers)
        assert user_response.status_code == status.HTTP_200_OK
        
        response_data = user_response.json()
        assert response_data["email"] == user_data["email"]
        assert response_data["name"] == user_data["name"]