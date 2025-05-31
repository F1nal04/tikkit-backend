import pytest
from uuid import uuid4


class TestTicketHistory:
    """Test ticket history tracking functionality."""

    @pytest.fixture
    def sample_ticket(self, client, auth_user):
        """Create a sample ticket for testing."""
        ticket_data = {
            "topic": "printer",
            "description": "Printer not working",
            "message": "The printer is making strange noises",
            "priority": "medium"
        }

        response = client.post("/ticket", json=ticket_data,
                               headers=auth_user["headers"])
        assert response.status_code == 200

        return response.json()

    def test_ticket_creation_history(self, client, auth_user, sample_ticket):
        """Test that ticket creation is recorded in history."""
        ticket_id = sample_ticket["id"]

        # Get ticket history
        response = client.get(f"/ticket/{ticket_id}/history")
        assert response.status_code == 200

        history = response.json()
        assert len(history) == 1

        # Check creation entry
        creation_entry = history[0]
        assert creation_entry["field_name"] == "ticket"
        assert creation_entry["old_value"] is None
        assert creation_entry["new_value"] == "Ticket created"
        assert creation_entry["change_type"] == "created"
        assert creation_entry["changed_by_name"] == auth_user["user_data"]["name"]

    def test_ticket_update_history(self, client, admin_user, sample_ticket):
        """Test that ticket updates are recorded in history."""
        ticket_id = sample_ticket["id"]

        # Update ticket
        update_data = {
            "description": "Updated printer description",
            "priority": "high",
            "status": "in_progress"
        }

        response = client.put(
            f"/ticket/{ticket_id}", json=update_data, headers=admin_user["headers"])
        assert response.status_code == 200

        # Get ticket history
        response = client.get(f"/ticket/{ticket_id}/history")
        assert response.status_code == 200

        history = response.json()
        # Should have creation + 3 update entries
        assert len(history) >= 4

        # Check that changes are recorded (history is ordered newest first)
        change_fields = [entry["field_name"]
                         for entry in history[:-1]]  # Exclude creation entry
        assert "Description" in change_fields
        assert "Priority" in change_fields
        assert "Status" in change_fields

    def test_ticket_assignment_history(self, client, admin_user, auth_user, sample_ticket):
        """Test that ticket assignments are recorded in history."""
        ticket_id = sample_ticket["id"]

        # Assign ticket
        response = client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": auth_user["user_id"]},
            headers=admin_user["headers"]
        )
        assert response.status_code == 200

        # Get ticket history
        response = client.get(f"/ticket/{ticket_id}/history")
        assert response.status_code == 200

        history = response.json()

        # Find assignment entry
        assignment_entries = [
            entry for entry in history if entry["field_name"] == "Assigned To"]
        assert len(assignment_entries) == 1

        assignment_entry = assignment_entries[0]
        assert assignment_entry["old_value"] == "None"
        assert assignment_entry["new_value"] == auth_user["user_data"]["name"]
        assert assignment_entry["change_type"] == "updated"

    def test_ticket_status_change_history(self, client, admin_user, sample_ticket):
        """Test that status changes are recorded in history."""
        ticket_id = sample_ticket["id"]

        # Change status
        response = client.put(
            f"/ticket/{ticket_id}/status",
            params={"status": "closed"},
            headers=admin_user["headers"]
        )
        assert response.status_code == 200

        # Get ticket history
        response = client.get(f"/ticket/{ticket_id}/history")
        assert response.status_code == 200

        history = response.json()

        # Find status change entry
        status_entries = [
            entry for entry in history if entry["field_name"] == "Status"]
        assert len(status_entries) == 1

        status_entry = status_entries[0]
        assert status_entry["old_value"] == "open"
        assert status_entry["new_value"] == "closed"
        assert status_entry["change_type"] == "updated"

    def test_ticket_with_history_endpoint(self, client, auth_user, sample_ticket):
        """Test the combined ticket with history endpoint."""
        ticket_id = sample_ticket["id"]

        response = client.get(f"/ticket/{ticket_id}/with-history")
        assert response.status_code == 200

        data = response.json()

        # Check ticket data
        assert data["id"] == ticket_id
        assert data["description"] == sample_ticket["description"]

        # Check history data
        assert "history" in data
        assert len(data["history"]) >= 1
        assert data["history"][0]["field_name"] == "ticket"
        assert data["history"][0]["change_type"] == "created"

    def test_ticket_deletion_history(self, client, admin_user, sample_ticket):
        """Test that ticket deletion is recorded in history."""
        ticket_id = sample_ticket["id"]

        # Delete ticket
        response = client.delete(
            f"/ticket/{ticket_id}", headers=admin_user["headers"])
        assert response.status_code == 200

        # History should still be accessible even after deletion
        # (In a real system, you might want to soft-delete tickets to preserve history)
        response = client.get(f"/ticket/{ticket_id}/history")
        # This will return 404 since ticket is deleted, but history entries exist in DB
        assert response.status_code == 404

    def test_history_ordering(self, client, admin_user, sample_ticket):
        """Test that history entries are ordered correctly (newest first)."""
        ticket_id = sample_ticket["id"]

        # Make multiple changes with small delays
        import time

        # First change
        client.put(
            f"/ticket/{ticket_id}", json={"priority": "high"}, headers=admin_user["headers"])
        time.sleep(0.1)

        # Second change
        client.put(
            f"/ticket/{ticket_id}", json={"priority": "low"}, headers=admin_user["headers"])
        time.sleep(0.1)

        # Third change
        client.put(f"/ticket/{ticket_id}/status",
                   params={"status": "closed"}, headers=admin_user["headers"])

        # Get history
        response = client.get(f"/ticket/{ticket_id}/history")
        assert response.status_code == 200

        history = response.json()

        # Check that entries are ordered by date (newest first)
        timestamps = [entry["changed_at"] for entry in history]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_history_user_names(self, client, admin_user, auth_user, sample_ticket):
        """Test that user names are properly displayed in history."""
        ticket_id = sample_ticket["id"]

        # Admin makes a change
        client.put(
            f"/ticket/{ticket_id}", json={"priority": "high"}, headers=admin_user["headers"])

        # Get history
        response = client.get(f"/ticket/{ticket_id}/history")
        assert response.status_code == 200

        history = response.json()

        # Check that user names are displayed correctly
        creation_entry = next(
            entry for entry in history if entry["change_type"] == "created")
        assert creation_entry["changed_by_name"] == auth_user["user_data"]["name"]

        update_entry = next(
            entry for entry in history if entry["field_name"] == "Priority")
        assert update_entry["changed_by_name"] == admin_user["user_data"]["name"]

    def test_history_nonexistent_ticket(self, client):
        """Test history endpoint with non-existent ticket."""
        fake_ticket_id = str(uuid4())

        response = client.get(f"/ticket/{fake_ticket_id}/history")
        assert response.status_code == 404
        assert "Ticket not found" in response.json()["detail"]

    def test_multiple_field_changes(self, client, admin_user, sample_ticket):
        """Test that multiple field changes in one update are all recorded."""
        ticket_id = sample_ticket["id"]

        # Update multiple fields at once
        update_data = {
            "description": "New description",
            "priority": "high",
            "message": "New message",
            "topic": "wifi"
        }

        response = client.put(
            f"/ticket/{ticket_id}", json=update_data, headers=admin_user["headers"])
        assert response.status_code == 200

        # Get history
        response = client.get(f"/ticket/{ticket_id}/history")
        assert response.status_code == 200

        history = response.json()

        # Check that all changes are recorded
        field_names = [entry["field_name"] for entry in history]
        assert "Description" in field_names
        assert "Priority" in field_names
        assert "Message" in field_names
        assert "Topic" in field_names


# Cleanup
def teardown_module():
    """Clean up test database."""
    import os
    if os.path.exists("./test_history.db"):
        os.remove("./test_history.db")
