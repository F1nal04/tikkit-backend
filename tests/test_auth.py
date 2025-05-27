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
        assert "Password must be at least 8 characters long" in response.json()["detail"]
    
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