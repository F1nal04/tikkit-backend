import pytest
from fastapi import status
from uuid import uuid4


class TestTicketCRUD:
    """Integration tests for ticket CRUD operations."""

    def test_create_ticket_success(self, client, authenticated_user, test_ticket_data):
        """Test successful ticket creation."""
        response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["topic"] == test_ticket_data["topic"]
        assert data["description"] == test_ticket_data["description"]
        assert data["priority"] == test_ticket_data["priority"]
        assert data["message"] == test_ticket_data["message"]
        assert data["status"] == "open"
        assert data["author"] == authenticated_user["user_data"]["id"]
        assert "id" in data
        assert "created_at" in data

    def test_create_ticket_without_auth(self, client, test_ticket_data):
        """Test ticket creation without authentication fails."""
        response = client.post("/ticket", json=test_ticket_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_ticket_success(self, client, authenticated_user, test_ticket_data):
        """Test successful ticket retrieval."""
        # Create ticket first
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Read the ticket
        response = client.get(f"/ticket/{ticket_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == ticket_id
        assert data["description"] == test_ticket_data["description"]

    def test_read_nonexistent_ticket(self, client):
        """Test reading non-existent ticket returns 404."""
        fake_uuid = str(uuid4())
        response = client.get(f"/ticket/{fake_uuid}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_ticket_as_admin(self, client, authenticated_user, authenticated_admin, test_ticket_data):
        """Test ticket update by admin user."""
        # Create ticket as regular user
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Update ticket as admin
        update_data = {
            "description": "Updated description",
            "priority": "low"
        }
        response = client.put(f"/ticket/{ticket_id}", json=update_data, headers=authenticated_admin["headers"])
        
        if response.status_code != status.HTTP_200_OK:
            print(f"Error response: {response.status_code} - {response.json()}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["priority"] == "low"

    def test_update_ticket_as_regular_user(self, client, authenticated_user, test_ticket_data):
        """Test ticket update by regular user fails."""
        # Create ticket
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Try to update as regular user
        update_data = {"description": "Updated description"}
        response = client.put(f"/ticket/{ticket_id}", json=update_data, headers=authenticated_user["headers"])
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_ticket_as_admin(self, client, authenticated_admin, authenticated_user, test_ticket_data):
        """Test ticket deletion by admin user."""
        # Create ticket as regular user
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Delete ticket as admin
        response = client.delete(f"/ticket/{ticket_id}", headers=authenticated_admin["headers"])
        
        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"]
        
        # Verify ticket is deleted
        get_response = client.get(f"/ticket/{ticket_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_ticket_as_regular_user(self, client, authenticated_user, test_ticket_data):
        """Test ticket deletion by regular user fails."""
        # Create ticket
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Try to delete as regular user
        response = client.delete(f"/ticket/{ticket_id}", headers=authenticated_user["headers"])
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_assign_ticket_as_admin(self, client, authenticated_admin, authenticated_user, test_ticket_data):
        """Test ticket assignment by admin."""
        # Create ticket
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Assign ticket to user
        user_id = authenticated_user["user_data"]["id"]
        response = client.put(f"/ticket/{ticket_id}/assign?assigned_to={user_id}", headers=authenticated_admin["headers"])
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["assigned_to"] == user_id

    def test_self_assign_unassigned_ticket(self, client, authenticated_user, test_ticket_data):
        """Test user can self-assign unassigned ticket."""
        # Create ticket
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Self-assign ticket
        user_id = authenticated_user["user_data"]["id"]
        response = client.put(f"/ticket/{ticket_id}/assign?assigned_to={user_id}", headers=authenticated_user["headers"])
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["assigned_to"] == user_id

    def test_update_ticket_status_by_author(self, client, authenticated_user, test_ticket_data):
        """Test ticket author can close their ticket."""
        # Create ticket
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Close ticket as author
        response = client.put(f"/ticket/{ticket_id}/status?status=closed", headers=authenticated_user["headers"])
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "closed"

    def test_update_ticket_status_by_assigned_user(self, client, authenticated_admin, authenticated_user, test_ticket_data):
        """Test assigned user can update ticket status."""
        # Create and assign ticket
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        
        user_id = authenticated_user["user_data"]["id"]
        client.put(f"/ticket/{ticket_id}/assign?assigned_to={user_id}", headers=authenticated_admin["headers"])
        
        # Update status as assigned user
        response = client.put(f"/ticket/{ticket_id}/status?status=in_progress", headers=authenticated_user["headers"])
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "in_progress"

    def test_list_tickets_no_filters(self, client, authenticated_user, test_ticket_data):
        """Test listing all tickets without filters."""
        # Create multiple tickets
        for i in range(3):
            ticket_data = test_ticket_data.copy()
            ticket_data["description"] = f"Test ticket {i}"
            client.post("/ticket", json=ticket_data, headers=authenticated_user["headers"])
        
        # List tickets
        response = client.get("/tickets")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3
        assert all("id" in ticket for ticket in data)

    def test_list_tickets_with_status_filter(self, client, authenticated_user, test_ticket_data):
        """Test listing tickets with status filter."""
        # Create and close a ticket
        create_response = client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]
        client.put(f"/ticket/{ticket_id}/status?status=closed", headers=authenticated_user["headers"])
        
        # List closed tickets
        response = client.get("/tickets?status=closed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(ticket["status"] == "closed" for ticket in data)

    def test_list_tickets_with_priority_filter(self, client, authenticated_user):
        """Test listing tickets with priority filter."""
        # Create tickets with different priorities
        for priority in ["low", "medium", "high"]:
            ticket_data = {
                "topic": "wifi",
                "description": f"Test {priority} priority",
                "priority": priority,
                "message": "Test message"
            }
            client.post("/ticket", json=ticket_data, headers=authenticated_user["headers"])
        
        # List high priority tickets
        response = client.get("/tickets?priority=high")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(ticket["priority"] == "high" for ticket in data)

    def test_list_tickets_with_author_filter(self, client, authenticated_user, test_ticket_data):
        """Test listing tickets with author filter."""
        # Create ticket
        client.post("/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        
        # List tickets by author
        user_id = authenticated_user["user_data"]["id"]
        response = client.get(f"/tickets?author={user_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(ticket["author"] == user_id for ticket in data)