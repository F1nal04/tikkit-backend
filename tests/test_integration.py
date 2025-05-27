import pytest
from fastapi import status


class TestCrossEntityIntegration:
    """Integration tests for cross-entity relationships and workflows."""

    def test_complete_ticket_workflow(self, client, authenticated_admin):
        """Test complete ticket workflow from creation to closure."""

        # Register a worker user
        worker_data = {
            "email": "workflow_worker@test.com",
            "password": "WorkerPass123!",
            "name": "Workflow Worker"
        }
        worker_response = client.post("/register", json=worker_data)
        worker_token = worker_response.json()["access_token"]
        worker_headers = {"Authorization": f"Bearer {worker_token}"}

        # Get worker info
        worker_info_response = client.get("/user", headers=worker_headers)
        worker_id = worker_info_response.json()["id"]

        # Change worker role to worker
        role_data = {"new_role": "worker"}
        client.put(f"/user/{worker_id}/role", json=role_data,
                   headers=authenticated_admin["headers"])

        # Register a regular user (ticket author)
        user_data = {
            "email": "workflow_user@test.com",
            "password": "UserPass123!",
            "name": "Workflow User"
        }
        user_response = client.post("/register", json=user_data)
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Test ticket data
        ticket_data = {
            "topic": "wifi",
            "description": "Workflow test ticket",
            "priority": "high",
            "message": "Test workflow message"
        }

        # User creates a ticket
        create_response = client.post(
            "/ticket", json=ticket_data, headers=user_headers)
        assert create_response.status_code == status.HTTP_200_OK
        ticket = create_response.json()
        ticket_id = ticket["id"]

        # Verify ticket is created with correct author
        user_info_response = client.get("/user", headers=user_headers)
        user_id = user_info_response.json()["id"]
        assert ticket["author"] == user_id
        assert ticket["status"] == "open"
        assert ticket["assigned_to"] is None

        # Admin assigns ticket to worker
        assign_response = client.put(
            f"/ticket/{ticket_id}/assign?assigned_to={worker_id}",
            headers=authenticated_admin["headers"]
        )
# Debug line removed
        assert assign_response.status_code == status.HTTP_200_OK
        assigned_ticket = assign_response.json()
        assert assigned_ticket["assigned_to"] == worker_id

        # Worker updates ticket status to in_progress
        status_response = client.put(
            f"/ticket/{ticket_id}/status?status=in_progress",
            headers=worker_headers
        )
        assert status_response.status_code == status.HTTP_200_OK
        in_progress_ticket = status_response.json()
        assert in_progress_ticket["status"] == "in_progress"

        # Worker updates ticket status to resolved
        resolve_response = client.put(
            f"/ticket/{ticket_id}/status?status=resolved",
            headers=worker_headers
        )
        assert resolve_response.status_code == status.HTTP_200_OK
        resolved_ticket = resolve_response.json()
        assert resolved_ticket["status"] == "resolved"

        # Original user closes the ticket
        close_response = client.put(
            f"/ticket/{ticket_id}/status?status=closed",
            headers=user_headers
        )
        assert close_response.status_code == status.HTTP_200_OK
        closed_ticket = close_response.json()
        assert closed_ticket["status"] == "closed"

        # Verify final state
        final_ticket_response = client.get(f"/ticket/{ticket_id}")
        final_ticket = final_ticket_response.json()
        assert final_ticket["status"] == "closed"
        assert final_ticket["assigned_to"] == worker_id
        assert final_ticket["author"] == user_id

    def test_user_deletion_constraints(self, client, authenticated_admin, test_user_data, test_ticket_data):
        """Test user deletion is prevented when they have related tickets."""
        # Create user and ticket
        user_response = client.post("/register", json=test_user_data)
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        user_info_response = client.get("/user", headers=user_headers)
        user_id = user_info_response.json()["id"]

        # Create ticket as author
        create_response = client.post(
            "/ticket", json=test_ticket_data, headers=user_headers)
        ticket_id = create_response.json()["id"]

        # Try to delete user (should fail - has authored tickets)
        delete_response = client.delete(
            f"/user/{user_id}", headers=authenticated_admin["headers"])
        assert delete_response.status_code == status.HTTP_400_BAD_REQUEST
        assert "tickets as author" in delete_response.json()["detail"]

        # Delete the ticket first
        client.delete(f"/ticket/{ticket_id}",
                      headers=authenticated_admin["headers"])

        # Now user deletion should succeed
        delete_response = client.delete(
            f"/user/{user_id}", headers=authenticated_admin["headers"])
        assert delete_response.status_code == status.HTTP_200_OK

    def test_ticket_assignment_workflows(self, client, authenticated_admin, test_user_data, test_ticket_data):
        """Test various ticket assignment scenarios."""
        # Create two users
        user1_data = test_user_data.copy()
        user1_data["email"] = "user1@example.com"
        user1_response = client.post("/register", json=user1_data)
        user1_token = user1_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user1_info = client.get("/user", headers=user1_headers).json()
        user1_id = user1_info["id"]

        user2_data = test_user_data.copy()
        user2_data["email"] = "user2@example.com"
        user2_response = client.post("/register", json=user2_data)
        user2_token = user2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        user2_info = client.get("/user", headers=user2_headers).json()
        user2_id = user2_info["id"]

        # User1 creates ticket
        create_response = client.post(
            "/ticket", json=test_ticket_data, headers=user1_headers)
        ticket_id = create_response.json()["id"]

        # User1 can self-assign their own ticket
        self_assign_response = client.put(
            f"/ticket/{ticket_id}/assign?assigned_to={user1_id}",
            headers=user1_headers
        )
        assert self_assign_response.status_code == status.HTTP_200_OK

        # User2 cannot steal assignment from User1
        steal_assign_response = client.put(
            f"/ticket/{ticket_id}/assign?assigned_to={user2_id}",
            headers=user2_headers
        )
        assert steal_assign_response.status_code == status.HTTP_403_FORBIDDEN

        # Admin can reassign ticket
        admin_reassign_response = client.put(
            f"/ticket/{ticket_id}/assign?assigned_to={user2_id}",
            headers=authenticated_admin["headers"]
        )
        assert admin_reassign_response.status_code == status.HTTP_200_OK

    def test_permission_escalation_prevention(self, client, test_user_data):
        """Test that users cannot escalate their own permissions."""
        # Register regular user
        user_response = client.post("/register", json=test_user_data)
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        user_info_response = client.get("/user", headers=user_headers)
        user_id = user_info_response.json()["id"]

        # Try to make themselves admin
        role_data = {"new_role": "admin"}
        escalate_response = client.put(
            f"/user/{user_id}/role", json=role_data, headers=user_headers)
        assert escalate_response.status_code == status.HTTP_403_FORBIDDEN

        # Verify role didn't change
        final_user_response = client.get("/user", headers=user_headers)
        assert final_user_response.json()["role"] == "user"

    def test_ticket_filtering_and_relationships(self, client, authenticated_admin, test_user_data):
        """Test ticket filtering works correctly with user relationships."""
        # Create multiple users
        users = []
        for i in range(3):
            user_data = test_user_data.copy()
            user_data["email"] = f"user{i}@example.com"
            user_response = client.post("/register", json=user_data)
            # Debug print
            print(
                f"User registration response for {user_data['email']}: {user_response.json()}")
            user_token = user_response.json()["access_token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}
            user_info = client.get("/user", headers=user_headers).json()
            users.append({
                "id": user_info["id"],
                "headers": user_headers
            })

        # Each user creates tickets with different priorities
        priorities = ["low", "medium", "high"]
        ticket_ids = []

        for i, (user, priority) in enumerate(zip(users, priorities)):
            ticket_data = {
                "topic": "wifi",
                "description": f"Ticket by user {i}",
                "priority": priority,
                "message": f"Test message {i}"
            }
            create_response = client.post(
                "/ticket", json=ticket_data, headers=user["headers"])
            ticket_ids.append(create_response.json()["id"])

        # Assign tickets to different users
        for i, ticket_id in enumerate(ticket_ids):
            assigned_user_id = users[(i + 1) %
                                     len(users)]["id"]  # Rotate assignments
            client.put(f"/ticket/{ticket_id}/assign?assigned_to={assigned_user_id}",
                       headers=authenticated_admin["headers"])

        # Test filtering by author
        author_filter_response = client.get(
            f"/tickets?author={users[0]['id']}")
        author_tickets = author_filter_response.json()
        assert len(author_tickets) == 1
        assert author_tickets[0]["author"] == users[0]["id"]

        # Test filtering by assigned_to
        assigned_filter_response = client.get(
            f"/tickets?assigned_to={users[1]['id']}")
        assigned_tickets = assigned_filter_response.json()
        assert len(assigned_tickets) == 1
        assert assigned_tickets[0]["assigned_to"] == users[1]["id"]

        # Test filtering by priority
        priority_filter_response = client.get("/tickets?priority=high")
        priority_tickets = priority_filter_response.json()
        assert all(ticket["priority"] == "high" for ticket in priority_tickets)

    def test_ai_endpoint_access_control(self, client, authenticated_admin, authenticated_user, test_ticket_data):
        """Test AI endpoint is only accessible to admins."""
        # Create a ticket
        create_response = client.post(
            "/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]

        # Regular user should not be able to access AI endpoint
        ai_response = client.get(
            f"/ai_request/{ticket_id}", headers=authenticated_user["headers"])
        assert ai_response.status_code == status.HTTP_403_FORBIDDEN

        # Admin should be able to access AI endpoint (even if it fails due to missing API key)
        admin_ai_response = client.get(
            f"/ai_request/{ticket_id}", headers=authenticated_admin["headers"])
        # We expect this to either succeed or fail with a different error (not 403)
        assert admin_ai_response.status_code != status.HTTP_403_FORBIDDEN

    def test_database_transaction_integrity(self, client, authenticated_user, test_ticket_data):
        """Test that database operations maintain integrity."""
        # Create ticket
        create_response = client.post(
            "/ticket", json=test_ticket_data, headers=authenticated_user["headers"])
        ticket_id = create_response.json()["id"]

        # Verify ticket exists in database
        get_response = client.get(f"/ticket/{ticket_id}")
        assert get_response.status_code == status.HTTP_200_OK

        # Verify ticket shows up in listings
        list_response = client.get("/tickets")
        ticket_ids = [ticket["id"] for ticket in list_response.json()]
        assert ticket_id in ticket_ids

        # Verify author relationship is correct
        user_info = client.get(
            "/user", headers=authenticated_user["headers"]).json()
        author_tickets = client.get(
            f"/tickets?author={user_info['id']}").json()
        assert any(ticket["id"] == ticket_id for ticket in author_tickets)
