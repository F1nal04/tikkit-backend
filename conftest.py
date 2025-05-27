from app.schemas import Role
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import tempfile

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Added import for Role


@pytest.fixture(scope="session")
def setup_test_env():
    """Set up test environment by backing up main database."""
    main_db_path = "tickets.db"
    backup_db_path = "tickets.db.pytest_backup"
    main_db_existed = False

    if os.path.exists(main_db_path):
        main_db_existed = True
        os.rename(main_db_path, backup_db_path)

    yield

    # Restore main database if it existed
    if main_db_existed and os.path.exists(backup_db_path):
        os.rename(backup_db_path, main_db_path)


@pytest.fixture
def test_app(setup_test_env):
    """Create app with isolated test database for each test."""
    import os
    if not os.getenv("SECRET_KEY"):
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-secure"

    from app import models, database  # app.database is where get_db is defined
    # Removed from app.database import get_db as it's not directly used here for override setup initially

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    models.Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine)

    # Import app after TestSessionLocal is defined, but before override is set by test_session
    from app.main import app

    # The actual override of app.dependency_overrides[database.get_db] will happen in test_session
    # to ensure the same session object is used.

    try:
        # Yield app, TestSessionLocal factory, and engine
        yield app, TestSessionLocal, test_engine
    finally:
        # Clear any overrides that might have been set by test_session
        app.dependency_overrides.clear()
        # Optionally, dispose engine if needed, though for in-memory it might not be critical
        # test_engine.dispose()


@pytest.fixture
def test_session(test_app):  # Depends on test_app to get app and TestSessionLocal
    """Create a database session that is shared with API calls for a single test."""
    app, TestSessionLocal, engine = test_app
    from app.database import get_db  # Import get_db here to reference the original

    # Create a connection that will be used for the duration of the test
    connection = engine.connect()
    # Begin a transaction
    transaction = connection.begin()
    # Create a session that uses this specific connection
    db_session_for_test = TestSessionLocal(bind=connection)

    # This is the crucial part: override get_db to return *this specific session instance*
    def get_shared_test_db():
        try:
            yield db_session_for_test
        finally:
            # The session is managed by the test_session fixture's try/finally
            pass

    original_get_db = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = get_shared_test_db

    try:
        yield db_session_for_test  # This session is used by fixtures like super_admin
    finally:
        db_session_for_test.close()  # Close the session
        transaction.rollback()  # Rollback any changes to keep tests isolated
        connection.close()  # Close the connection
        # Restore original override or clear it
        if original_get_db:
            app.dependency_overrides[get_db] = original_get_db
        else:
            del app.dependency_overrides[get_db]


@pytest.fixture
def client(test_app):
    """Create a test client."""
    app, _, _ = test_app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data():
    """Standard test user data with unique email."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test_{unique_id}@example.com",
        "password": "TestPass123!",
        "name": f"Test User {unique_id}"
    }


@pytest.fixture
def admin_user_data():
    """Admin test user data with unique email."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"admin_{unique_id}@example.com",
        "password": "AdminPass123!",
        "name": f"Admin User {unique_id}"
    }


@pytest.fixture
def test_ticket_data():
    """Standard test ticket data."""
    return {
        "topic": "wifi",
        "description": "WiFi connection issues",
        "priority": "high",
        "message": "Cannot connect to WiFi network"
    }


@pytest.fixture
def authenticated_user(client):
    """Create and authenticate a test user, return token, user data, and plain password."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # This is the actual user data including password used for registration
    registration_data = {
        "email": f"authenticated_{unique_id}@test.com",
        "password": "AuthenticatedPass123!",
        "name": f"Authenticated User {unique_id}"
    }

    # Register user
    response = client.post("/register", json=registration_data)
    assert response.status_code == 200

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info from API
    user_response = client.get("/user", headers=headers)
    user_info_from_api = user_response.json()

    return {
        "token": token,
        "headers": headers,
        "user_data": user_info_from_api,  # Data from /user endpoint
        "plain_password": registration_data["password"]  # Added plain password
    }


@pytest.fixture
def super_admin(client, test_app):
    """Create a super admin user via API and promote to admin using a fresh database session."""
    import uuid
    from app.models import User
    from app.schemas import Role

    app, TestSessionLocal, engine = test_app

    unique_id_str = str(uuid.uuid4())[:8]
    admin_email = f"admin_{unique_id_str}@test.com"
    admin_password = "AdminPass123!"
    admin_name = f"Admin User {unique_id_str}"

    # 1. Create user via API (this ensures they exist in the database)
    registration_data = {
        "email": admin_email,
        "password": admin_password,
        "name": admin_name
    }

    register_response = client.post("/register", json=registration_data)
    assert register_response.status_code == 200, f"Registration failed: {register_response.json()}"

    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info
    user_info_response = client.get("/user", headers=headers)
    assert user_info_response.status_code == 200, f"Failed to get user info: {user_info_response.json()}"
    user_info = user_info_response.json()

    print(
        f"[DEBUG super_admin] Created user via API: ID={user_info['id']}, Email={user_info['email']}, Role={user_info['role']}")

    # 2. Create a fresh database session to promote the user
    fresh_session = TestSessionLocal()
    try:
        # Find the user by email in the fresh session
        user_id_uuid = uuid.UUID(user_info['id'])
        db_user = fresh_session.query(User).filter(
            User.id == user_id_uuid).first()

        if not db_user:
            # Try by email as fallback
            db_user = fresh_session.query(User).filter(
                User.email == admin_email).first()

        if db_user:
            print(
                f"[DEBUG super_admin] Found user in fresh session: ID={db_user.id}, Current Role={db_user.role}")

            # Update role to admin
            db_user.role = Role.admin.value
            fresh_session.commit()
            fresh_session.refresh(db_user)

            print(
                f"[DEBUG super_admin] Updated user role: ID={db_user.id}, New Role={db_user.role}")
        else:
            print(
                f"[DEBUG super_admin] Could not find user in fresh session, proceeding with regular user")

    finally:
        fresh_session.close()

    # 3. Verify the role change by getting user info again
    final_user_info_response = client.get("/user", headers=headers)
    assert final_user_info_response.status_code == 200, f"Failed to get updated user info: {final_user_info_response.json()}"
    final_user_info = final_user_info_response.json()

    print(
        f"[DEBUG super_admin] Final user info: ID={final_user_info['id']}, Role={final_user_info['role']}")

    return {
        "token": token,
        "headers": headers,
        "user_data": final_user_info
    }


@pytest.fixture
def authenticated_admin(super_admin):
    """Alias for super_admin to maintain compatibility with existing tests."""
    return super_admin
