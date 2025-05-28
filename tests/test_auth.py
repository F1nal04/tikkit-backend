import pytest


class TestRegisterEndpoint:
    """Test cases for the /register endpoint"""

    def test_register_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "TestPass123!"
        }

        response = client.post("/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        user_data = {
            "email": "test2@example.com",
            "name": "Test User",
            "password": "weak"
        }

        response = client.post("/register", json=user_data)

        assert response.status_code == 400
        assert "Password must be at least 8 characters long" in response.json()[
            "detail"]

    def test_register_duplicate_email(self, client):
        """Test registration with already registered email"""
        user_data = {
            "email": "duplicate@example.com",
            "name": "Test User",
            "password": "TestPass123!"
        }

        # First registration
        response1 = client.post("/register", json=user_data)
        assert response1.status_code == 200

        # Second registration with same email
        response2 = client.post("/register", json=user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        incomplete_data = {
            "email": "test3@example.com"
            # Missing name and password
        }

        response = client.post("/register", json=incomplete_data)
        assert response.status_code == 422  # Validation error

    def test_register_password_strength_edge_cases(self, client):
        """Test password strength validation edge cases"""
        base_user = {
            "email": "pwtest@example.com",
            "name": "Password Test User"
        }

        # Exactly 8 characters but no special chars
        user_data = {**base_user, "email": "pw1@example.com",
                     "password": "Password"}
        response = client.post("/register", json=user_data)
        assert response.status_code == 400

        # 8 characters, no numbers
        user_data = {**base_user, "email": "pw2@example.com",
                     "password": "Password!"}
        response = client.post("/register", json=user_data)
        assert response.status_code == 400

        # 8 characters, no special chars
        user_data = {**base_user, "email": "pw3@example.com",
                     "password": "Password1"}
        response = client.post("/register", json=user_data)
        assert response.status_code == 400

        # Valid: exactly 8 chars with number and special char
        user_data = {**base_user, "email": "pw4@example.com",
                     "password": "Pass123!"}
        response = client.post("/register", json=user_data)
        assert response.status_code == 200

    def test_register_email_validation(self, client):
        """Test email format validation"""
        base_user = {
            "name": "Email Test User",
            "password": "ValidPass123!"
        }

        invalid_emails = [
            "notanemail",
            "@domain.com",
            "user@",
            "user.domain.com",
            "user@.com",
            "user..name@domain.com",
            "user@domain",
            ""
        ]

        for email in invalid_emails:
            user_data = {**base_user, "email": email}
            response = client.post("/register", json=user_data)
            assert response.status_code == 422, f"Email '{email}' should be invalid but got status {response.status_code}"

    def test_register_field_length_validation(self, client):
        """Test field length boundary validation"""
        # Very long email
        long_email = "a" * 300 + "@example.com"
        user_data = {
            "email": long_email,
            "name": "Test User",
            "password": "ValidPass123!"
        }
        response = client.post("/register", json=user_data)
        # Should either succeed or fail gracefully with validation error
        assert response.status_code in [200, 422]

        # Very long name
        long_name = "A" * 1000
        user_data = {
            "email": "longname@example.com",
            "name": long_name,
            "password": "ValidPass123!"
        }
        response = client.post("/register", json=user_data)
        assert response.status_code in [200, 422]

    def test_register_special_characters(self, client):
        """Test registration with special characters in name"""
        special_names = [
            "José García",
            "李明",
            "John O'Connor",
            "Anne-Marie",
            "René François"
        ]

        for i, name in enumerate(special_names):
            user_data = {
                "email": f"special{i}@example.com",
                "name": name,
                "password": "ValidPass123!"
            }
            response = client.post("/register", json=user_data)
            assert response.status_code == 200, f"Name '{name}' should be valid but got status {response.status_code}"

    def test_register_empty_vs_null_fields(self, client):
        """Test registration with empty vs null field values"""
        # Empty string values
        user_data = {
            "email": "",
            "name": "",
            "password": ""
        }
        response = client.post("/register", json=user_data)
        assert response.status_code == 422, f"Empty string values should be unprocessable but got status {response.status_code}"

        # None values
        user_data = {
            "email": None,
            "name": None,
            "password": None
        }
        response = client.post("/register", json=user_data)
        assert response.status_code == 422, f"Null values should be unprocessable but got status {response.status_code}"


class TestTokenEndpoint:
    """Test cases for the /token endpoint"""

    def test_login_success(self, client):
        """Test successful login"""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "name": "Login User",
            "password": "LoginPass123!"
        }
        register_response = client.post("/register", json=user_data)
        assert register_response.status_code == 200

        # Now login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }

        response = client.post("/token", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_email(self, client):
        """Test login with non-existent email"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "SomePassword123!"
        }

        response = client.post("/token", data=login_data)

        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        # First register a user
        user_data = {
            "email": "wrongpass@example.com",
            "name": "Wrong Pass User",
            "password": "CorrectPass123!"
        }
        register_response = client.post("/register", json=user_data)
        assert register_response.status_code == 200

        # Try with wrong password
        login_data = {
            "username": user_data["email"],
            "password": "WrongPassword123!"
        }

        response = client.post("/token", data=login_data)

        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post("/token", data={})

        assert response.status_code == 422  # Validation error

    def test_login_empty_password(self, client):
        """Test login with empty password"""
        # First register a user
        user_data = {
            "email": "emptypass@example.com",
            "name": "Empty Pass User",
            "password": "ValidPass123!"
        }
        register_response = client.post("/register", json=user_data)
        assert register_response.status_code == 200

        # Try with empty password
        login_data = {
            "username": user_data["email"],
            "password": ""
        }

        response = client.post("/token", data=login_data)

        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_case_sensitivity(self, client):
        """Test email case sensitivity in login"""
        # Register with lowercase email
        user_data = {
            "email": "case@example.com",
            "name": "Case Test User",
            "password": "CasePass123!"
        }
        register_response = client.post("/register", json=user_data)
        assert register_response.status_code == 200

        # Try login with different cases
        test_cases = [
            "case@example.com",  # original
            "CASE@EXAMPLE.COM",  # uppercase
            "Case@Example.Com",  # mixed case
        ]

        for email in test_cases:
            login_data = {
                "username": email,
                "password": user_data["password"]
            }
            response = client.post("/token", data=login_data)
            # Email should be case insensitive
            assert response.status_code == 200, f"Login with email '{email}' should succeed"

    def test_login_with_very_long_credentials(self, client):
        """Test login with extremely long credentials"""
        # Very long username
        long_username = "a" * 1000 + "@example.com"
        login_data = {
            "username": long_username,
            "password": "password"
        }
        response = client.post("/token", data=login_data)
        assert response.status_code in [400, 422], f"Very long username should be handled gracefully but got status {response.status_code}"

        # Very long password
        long_password = "a" * 1000
        login_data = {
            "username": "test@example.com",
            "password": long_password
        }
        response = client.post("/token", data=login_data)
        assert response.status_code in [400, 422], f"Very long password should be handled gracefully but got status {response.status_code}"


class TestAuthenticationFlow:
    """Test complete authentication flow"""

    def test_register_then_login(self, client):
        """Test complete flow: register then login"""
        # Register
        user_data = {
            "email": "flow@example.com",
            "name": "Flow User",
            "password": "FlowPass123!"
        }

        register_response = client.post("/register", json=user_data)
        assert register_response.status_code == 200
        register_token = register_response.json()["access_token"]

        # Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }

        login_response = client.post("/token", data=login_data)
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]

        # Both tokens should be valid (though they may be different)
        assert isinstance(register_token, str) and len(register_token) > 0
        assert isinstance(login_token, str) and len(login_token) > 0
