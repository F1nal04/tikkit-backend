import pytest
from fastapi import status
from uuid import uuid4


class TestUserManagement:
    """Integration tests for user management operations."""

    def test_get_current_user_info(self, client, authenticated_user):
        """Test getting current user info."""
        response = client.get("/user", headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == authenticated_user["user_data"]["id"]
        assert data["email"] == authenticated_user["user_data"]["email"]
        assert data["name"] == authenticated_user["user_data"]["name"]
        assert "hashed_password" not in data  # Password should not be exposed

    def test_get_user_by_id(self, client, authenticated_user):
        """Test getting user by ID."""
        user_id = authenticated_user["user_data"]["id"]
        response = client.get(f"/user?user_id={user_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user_id

    def test_get_nonexistent_user(self, client):
        """Test getting non-existent user returns 404."""
        fake_uuid = str(uuid4())
        response = client.get(f"/user?user_id={fake_uuid}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_own_user_info(self, client, authenticated_user):
        """Test user can update their own information."""
        user_id = authenticated_user["user_data"]["id"]
        update_data = {"name": "Updated Name"}

        response = client.put(
            f"/user/{user_id}", json=update_data, headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_other_user_as_regular_user(self, client, authenticated_user, test_session):
        """Test regular user cannot update other users."""
        from app.models import User
        from app.security import get_password_hash

        # Create another user
        other_user = User(
            email="other@example.com",
            name="Other User",
            hashed_password=get_password_hash("password123!")
        )
        test_session.add(other_user)
        test_session.commit()
        test_session.refresh(other_user)

        # Try to update other user
        update_data = {"name": "Hacked Name"}
        response = client.put(
            f"/user/{other_user.id}", json=update_data, headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_as_admin(self, client, authenticated_admin, authenticated_user):
        """Test admin can update any user."""
        user_id = authenticated_user["user_data"]["id"]
        update_data = {"name": "Admin Updated Name"}

        response = client.put(
            f"/user/{user_id}", json=update_data, headers=authenticated_admin["headers"])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Admin Updated Name"

    def test_delete_own_user(self, client, test_user_data):
        """Test user can delete their own account when they have no tickets."""
        # Register new user
        register_response = client.post("/register", json=test_user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get user info
        user_response = client.get("/user", headers=headers)
        user_id = user_response.json()["id"]

        # Delete own account
        response = client.delete(f"/user/{user_id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"]

    def test_delete_user_with_authored_tickets(self, client, authenticated_user, test_ticket_data):
        """Test cannot delete user who authored tickets."""
        # Create a ticket
        client.post("/ticket", json=test_ticket_data,
                    headers=authenticated_user["headers"])

        # Try to delete user
        user_id = authenticated_user["user_data"]["id"]
        response = client.delete(
            f"/user/{user_id}", headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "tickets as author" in response.json()["detail"]

    def test_delete_user_with_assigned_tickets(self, client, authenticated_admin, authenticated_user, test_ticket_data):
        """Test cannot delete user with assigned tickets."""
        # Create and assign ticket
        create_response = client.post(
            "/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]

        user_id = authenticated_user["user_data"]["id"]
        client.put(f"/ticket/{ticket_id}/assign?assigned_to={user_id}",
                   headers=authenticated_admin["headers"])

        # Try to delete user
        response = client.delete(
            f"/user/{user_id}", headers=authenticated_admin["headers"])

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "tickets assigned" in response.json()["detail"]

    def test_change_own_password(self, client, authenticated_user):
        """Test user can change their own password."""
        user_id = authenticated_user["user_data"]["id"]
        password_data = {
            "old_password": authenticated_user["plain_password"],
            "new_password": "NewPass123!"
        }

        response = client.put(
            f"/user/{user_id}/password", json=password_data, headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_200_OK
        assert "Password changed successfully" in response.json()["message"]

        # Verify can login with new password
        login_data = {
            "username": authenticated_user["user_data"]["email"],
            "password": "NewPass123!"
        }
        login_response = client.post("/token", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK

    def test_change_password_with_wrong_old_password(self, client, authenticated_user):
        """Test changing password with wrong old password fails."""
        user_id = authenticated_user["user_data"]["id"]
        password_data = {
            "old_password": "wrongpassword",
            "new_password": "NewPass123!"
        }

        response = client.put(
            f"/user/{user_id}/password", json=password_data, headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Old password is incorrect" in response.json()["detail"]

    def test_admin_change_user_password_without_old_password(self, client, authenticated_admin, authenticated_user):
        """Test admin can change user password without knowing old password."""
        user_id = authenticated_user["user_data"]["id"]
        password_data = {
            "old_password": "",  # Admin doesn't need old password
            "new_password": "AdminSetPass123!"
        }

        response = client.put(
            f"/user/{user_id}/password", json=password_data, headers=authenticated_admin["headers"])

        assert response.status_code == status.HTTP_200_OK

    def test_change_own_email(self, client, authenticated_user):
        """Test user can change their own email."""
        user_id = authenticated_user["user_data"]["id"]
        email_data = {
            "password": authenticated_user["plain_password"],
            "new_email": "newemail@example.com"
        }

        response = client.put(
            f"/user/{user_id}/email", json=email_data, headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_change_email_with_wrong_password(self, client, authenticated_user):
        """Test changing email with wrong password fails."""
        user_id = authenticated_user["user_data"]["id"]
        email_data = {
            "password": "wrongpassword",
            "new_email": "newemail@example.com"
        }

        response = client.put(
            f"/user/{user_id}/email", json=email_data, headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Password is incorrect" in response.json()["detail"]

    def test_admin_change_user_role(self, client, authenticated_admin, authenticated_user):
        """Test admin can change user roles."""
        user_id = authenticated_user["user_data"]["id"]
        role_data = {"new_role": "worker"}

        response = client.put(
            f"/user/{user_id}/role", json=role_data, headers=authenticated_admin["headers"])

        assert response.status_code == status.HTTP_200_OK
        assert "Role changed successfully" in response.json()["message"]

    def test_regular_user_cannot_change_roles(self, client, authenticated_user):
        """Test regular user cannot change roles."""
        user_id = authenticated_user["user_data"]["id"]
        role_data = {"new_role": "admin"}

        response = client.put(
            f"/user/{user_id}/role", json=role_data, headers=authenticated_user["headers"])

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_change_admin_role(self, client, authenticated_admin, test_session):
        """Test cannot change role of admin users."""
        from app.models import User
        from app.schemas import Role
        from app.security import get_password_hash

        # Create another admin user
        admin_user = User(
            email="admin2@example.com",
            name="Admin Two",
            hashed_password=get_password_hash("password123!"),
            role="admin"
        )
        test_session.add(admin_user)
        test_session.commit()
        test_session.refresh(admin_user)

        # Try to change admin role
        role_data = {"new_role": "user"}
        response = client.put(
            f"/user/{admin_user.id}/role", json=role_data, headers=authenticated_admin["headers"])

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cannot change role of admin users" in response.json()["detail"]

    def test_list_all_users(self, client, authenticated_user):
        """Test listing all users."""
        response = client.get("/users")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all("id" in user for user in data)
        assert all("hashed_password" not in user for user in data)

    def test_list_users_with_role_filter(self, client, authenticated_admin):
        """Test listing users with role filter."""
        response = client.get("/users?role=admin")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(user["role"] == "admin" for user in data)

    def test_list_users_pagination(self, client):
        """Test user listing pagination."""
        response = client.get("/users?skip=0&limit=1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 1
