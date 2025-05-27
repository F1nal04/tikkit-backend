import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_user(client):
    """Create and authenticate a test user"""
    user_data = {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "TestPass123!"
    }
    
    # Register user
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    return {"headers": headers, "user_data": user_data, "token": token}

@pytest.fixture
def admin_user(client):
    """Create and authenticate an admin user"""
    user_data = {
        "email": "admin@example.com",
        "name": "Admin User",
        "password": "AdminPass123!"
    }
    
    # Register user
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Note: In a real scenario, you'd need to promote this user to admin
    # For testing purposes, the admin fixture creates a regular user
    # The admin-specific tests may need adjustment based on your role management
    
    return {"headers": headers, "user_data": user_data, "token": token}