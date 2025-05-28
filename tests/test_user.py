import pytest
from uuid import uuid4


class TestUser:
    def test_get_user(self, client, auth_user):
        response = client.get("/user", headers=auth_user["headers"])
        assert response.status_code == 200
        assert response.json()["email"] == auth_user["user_data"]["email"]
        assert response.json()["name"] == auth_user["user_data"]["name"]
        assert response.json()["role"] == 'user'

    def test_get_user_by_id(self, client, auth_user):
        response = client.get("/user", headers=auth_user["headers"])
        assert response.status_code == 200
        user_id = response.json()["id"]

        response = client.get(
            "/user", params={"user_id": user_id})
        assert response.status_code == 200
        assert response.json()["email"] == auth_user["user_data"]["email"]
        assert response.json()["name"] == auth_user["user_data"]["name"]
        assert response.json()["role"] == 'user'

    def test_get_user_by_id_not_found(self, client):
        response = client.get(
            "/user", params={"user_id": "123e4567-e89b-12d3-a456-426614174000"})
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_get_user_unauthenticated(self, client):
        response = client.get("/user")
        assert response.status_code == 400
        assert response.json()[
            "detail"] == "No user_id provided and no authenticated user."

    def test_update_user_self(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        update_data = {"name": "Updated Name"}
        response = client.put(
            f"/user/{user_id}", json=update_data, headers=auth_user["headers"])
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["email"] == auth_user["user_data"]["email"]

    def test_update_user_admin_can_update_any(self, client, auth_user, admin_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        update_data = {"name": "Admin Updated Name"}
        response = client.put(
            f"/user/{user_id}", json=update_data, headers=admin_user["headers"])
        assert response.status_code == 200
        assert response.json()["name"] == "Admin Updated Name"

    def test_update_user_other_user_forbidden(self, client, auth_user, admin_user):
        admin_id = admin_user["user_id"]

        update_data = {"name": "Unauthorized Update"}
        response = client.put(
            f"/user/{admin_id}", json=update_data, headers=auth_user["headers"])
        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"

    def test_update_user_not_found(self, client, admin_user):
        fake_id = str(uuid4())
        update_data = {"name": "Updated Name"}
        response = client.put(
            f"/user/{fake_id}", json=update_data, headers=admin_user["headers"])
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_delete_user_self(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        response = client.delete(
            f"/user/{user_id}", headers=auth_user["headers"])
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"

    def test_delete_user_admin_can_delete_any(self, client, auth_user, admin_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        response = client.delete(
            f"/user/{user_id}", headers=admin_user["headers"])
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"

    def test_delete_user_other_user_forbidden(self, client, auth_user, admin_user):
        admin_id = admin_user["user_id"]

        response = client.delete(
            f"/user/{admin_id}", headers=auth_user["headers"])
        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"

    def test_delete_user_not_found(self, client, admin_user):
        fake_id = str(uuid4())
        response = client.delete(
            f"/user/{fake_id}", headers=admin_user["headers"])
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_delete_user_with_authored_tickets(self, client, auth_user, admin_user):
        # Create a ticket as the auth_user
        ticket_data = {
            "topic": "wifi",
            "description": "Test ticket",
            "message": "Test message",
            "priority": "medium"
        }
        client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        
        # Try to delete the user - should fail due to authored tickets
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        response = client.delete(f"/user/{user_id}", headers=admin_user["headers"])
        assert response.status_code == 400
        assert "Cannot delete user: user has 1 tickets as author" in response.json()["detail"]

    def test_delete_user_with_assigned_tickets(self, client, auth_user, admin_user):
        # Create a ticket and assign it to auth_user
        ticket_data = {
            "topic": "wifi",
            "description": "Test ticket",
            "message": "Test message",
            "priority": "medium"
        }
        ticket_response = client.post("/ticket", json=ticket_data, headers=admin_user["headers"])
        ticket_id = ticket_response.json()["id"]
        
        # Assign ticket to auth_user
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        client.put(f"/ticket/{ticket_id}/assign", params={"assigned_to": user_id}, headers=admin_user["headers"])
        
        # Try to delete the user - should fail due to assigned tickets
        response = client.delete(f"/user/{user_id}", headers=admin_user["headers"])
        assert response.status_code == 400
        assert "Cannot delete user: user has 1 tickets assigned to them" in response.json()["detail"]

    def test_change_password_self(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        password_data = {
            "old_password": auth_user["user_data"]["password"],
            "new_password": "NewPass123!"
        }
        response = client.put(
            f"/user/{user_id}/password", json=password_data, headers=auth_user["headers"])
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

    def test_change_password_wrong_old_password(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        password_data = {
            "old_password": "WrongPassword123!",
            "new_password": "NewPass123!"
        }
        response = client.put(
            f"/user/{user_id}/password", json=password_data, headers=auth_user["headers"])
        assert response.status_code == 400
        assert response.json()["detail"] == "Old password is incorrect"

    def test_change_password_admin_no_old_password_required(self, client, auth_user, admin_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        password_data = {
            "old_password": "AnyPassword",
            "new_password": "NewPass123!"
        }
        response = client.put(
            f"/user/{user_id}/password", json=password_data, headers=admin_user["headers"])
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

    def test_change_password_admin_changing_own_needs_old_password(self, client, admin_user):
        admin_id = admin_user["user_id"]
        
        # Admin changing their own password should require correct old password
        password_data = {
            "old_password": "WrongOldPassword",
            "new_password": "NewPass123!"
        }
        response = client.put(f"/user/{admin_id}/password", json=password_data, headers=admin_user["headers"])
        assert response.status_code == 400
        assert response.json()["detail"] == "Old password is incorrect"

    def test_change_password_unauthenticated(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        password_data = {
            "old_password": "password",
            "new_password": "NewPass123!"
        }
        response = client.put(f"/user/{user_id}/password", json=password_data)
        assert response.status_code == 401

    def test_change_password_not_found(self, client, admin_user):
        fake_id = str(uuid4())
        password_data = {
            "old_password": "password",
            "new_password": "NewPass123!"
        }
        response = client.put(f"/user/{fake_id}/password", json=password_data, headers=admin_user["headers"])
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_change_email_self(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        email_data = {
            "password": auth_user["user_data"]["password"],
            "new_email": "newemail@example.com"
        }
        response = client.put(
            f"/user/{user_id}/email", json=email_data, headers=auth_user["headers"])
        assert response.status_code == 200
        assert response.json()["email"] == "newemail@example.com"

    def test_change_email_wrong_password(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        email_data = {
            "password": "WrongPassword123!",
            "new_email": "newemail@example.com"
        }
        response = client.put(
            f"/user/{user_id}/email", json=email_data, headers=auth_user["headers"])
        assert response.status_code == 400
        assert response.json()["detail"] == "Password is incorrect"

    def test_change_email_admin_changing_others_no_password_required(self, client, auth_user, admin_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        email_data = {
            "password": "AnyPassword",
            "new_email": "admin_changed@example.com"
        }
        response = client.put(f"/user/{user_id}/email", json=email_data, headers=admin_user["headers"])
        assert response.status_code == 200
        assert response.json()["email"] == "admin_changed@example.com"

    def test_change_email_unauthenticated(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        email_data = {
            "password": "password",
            "new_email": "newemail@example.com"
        }
        response = client.put(f"/user/{user_id}/email", json=email_data)
        assert response.status_code == 401

    def test_change_email_not_found(self, client, admin_user):
        fake_id = str(uuid4())
        email_data = {
            "password": "password",
            "new_email": "newemail@example.com"
        }
        response = client.put(f"/user/{fake_id}/email", json=email_data, headers=admin_user["headers"])
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_change_role_admin_only(self, client, auth_user, admin_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]

        role_data = {"new_role": "worker"}
        response = client.put(
            f"/user/{user_id}/role", json=role_data, headers=admin_user["headers"])
        assert response.status_code == 200
        assert response.json()["message"] == "Role changed successfully"

    def test_change_role_non_admin_forbidden(self, client, auth_user, admin_user):
        admin_id = admin_user["user_id"]

        role_data = {"new_role": "worker"}
        response = client.put(
            f"/user/{admin_id}/role", json=role_data, headers=auth_user["headers"])
        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"

    def test_change_role_cannot_change_admin(self, client, admin_user):
        another_admin_data = {
            "email": "admin2@example.com",
            "name": "Admin User 2",
            "password": "AdminPass123!"
        }

        response = client.post("/register", json=another_admin_data)
        token = response.json()["access_token"]

        # Promote to admin first
        from tests.conftest import TestingSessionLocal
        from app.models import User
        from app.schemas import Role
        from uuid import UUID
        import jwt

        decoded_token = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded_token["sub"]

        db = TestingSessionLocal()
        try:
            user_uuid = UUID(user_id)
            db_user = db.get(User, user_uuid)
            db_user.role = Role.admin
            db.commit()
        finally:
            db.close()

        # Try to change admin role - should fail
        role_data = {"new_role": "worker"}
        response = client.put(
            f"/user/{user_id}/role", json=role_data, headers=admin_user["headers"])
        assert response.status_code == 403
        assert response.json()["detail"] == "Cannot change role of admin users"

    def test_change_role_unauthenticated(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        role_data = {"new_role": "worker"}
        response = client.put(f"/user/{user_id}/role", json=role_data)
        assert response.status_code == 401

    def test_change_role_not_found(self, client, admin_user):
        fake_id = str(uuid4())
        role_data = {"new_role": "worker"}
        response = client.put(f"/user/{fake_id}/role", json=role_data, headers=admin_user["headers"])
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_update_user_unauthenticated(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        update_data = {"name": "Updated Name"}
        response = client.put(f"/user/{user_id}", json=update_data)
        assert response.status_code == 401

    def test_delete_user_unauthenticated(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        response = client.delete(f"/user/{user_id}")
        assert response.status_code == 401


class TestUsers:
    def test_get_users_no_filter(self, client):
        response = client.get("/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_users_with_role_filter(self, client, auth_user, admin_user):
        response = client.get("/users", params={"role": "admin"})
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1
        for user in users:
            assert user["role"] == "admin"

    def test_get_users_with_pagination(self, client):
        response = client.get("/users", params={"skip": 0, "limit": 1})
        assert response.status_code == 200
        users = response.json()
        assert len(users) <= 1

    def test_get_users_invalid_role_filter(self, client):
        response = client.get("/users", params={"role": "invalid_role"})
        assert response.status_code == 422, f"Invalid role filter should return 422 but got {response.status_code}"

    def test_get_users_with_large_pagination(self, client):
        response = client.get("/users", params={"skip": 1000, "limit": 100})
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) == 0  # Should be empty for high skip value

    def test_user_update_partial_fields(self, client, auth_user):
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        original_email = user_response.json()["email"]
        
        # Test partial update - only name
        update_data = {"name": "Only Name Updated"}
        response = client.put(f"/user/{user_id}", json=update_data, headers=auth_user["headers"])
        assert response.status_code == 200
        assert response.json()["name"] == "Only Name Updated"
        assert response.json()["email"] == original_email  # Email should remain unchanged

    def test_user_operations_with_invalid_uuid(self, client, admin_user):
        invalid_uuid = "not-a-uuid"
        
        # Test various operations with invalid UUID
        update_data = {"name": "Test"}
        response = client.put(f"/user/{invalid_uuid}", json=update_data, headers=admin_user["headers"])
        assert response.status_code == 422, f"PUT with invalid UUID should return 422 but got {response.status_code}"
        
        response = client.delete(f"/user/{invalid_uuid}", headers=admin_user["headers"])
        assert response.status_code == 422, f"DELETE with invalid UUID should return 422 but got {response.status_code}"
        
        password_data = {"old_password": "test", "new_password": "NewPass123!"}
        response = client.put(f"/user/{invalid_uuid}/password", json=password_data, headers=admin_user["headers"])
        assert response.status_code == 422, f"Password change with invalid UUID should return 422 but got {response.status_code}"
