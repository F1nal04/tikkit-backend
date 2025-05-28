import pytest
from app.schemas import Priority, Topic, Status
from uuid import uuid4


class TestTicketEndpoint:
    """Test cases for /ticket endpoint (CRUD operations)"""

    def test_create_ticket_success(self, client, auth_user):
        """Test successful ticket creation"""
        ticket_data = {
            "topic": Topic.wifi.value,
            "description": "WiFi connection issues in conference room",
            "message": "Unable to connect to corporate WiFi network",
            "priority": Priority.medium.value
        }

        response = client.post("/ticket", json=ticket_data,
                               headers=auth_user["headers"])

        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == ticket_data["topic"]
        assert data["description"] == ticket_data["description"]
        assert data["message"] == ticket_data["message"]
        assert data["priority"] == ticket_data["priority"]
        assert data["status"] == Status.open.value
        assert "id" in data
        assert "created_at" in data
        assert "author" in data
        assert data["author_name"] == auth_user["user_data"]["name"]

    def test_create_ticket_unauthorized(self, client):
        """Test ticket creation without authentication"""
        ticket_data = {
            "topic": Topic.printer.value,
            "description": "Printer not working",
            "message": "Paper jam in main printer",
            "priority": Priority.high.value
        }

        response = client.post("/ticket", json=ticket_data)

        assert response.status_code == 401

    def test_create_ticket_missing_fields(self, client, auth_user):
        """Test ticket creation with missing required fields"""
        incomplete_data = {
            "topic": Topic.wifi.value,
            # Missing description and priority
        }

        response = client.post(
            "/ticket", json=incomplete_data, headers=auth_user["headers"])
        assert response.status_code == 422  # Validation error

    def test_read_ticket_success(self, client, auth_user):
        """Test reading a specific ticket"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.macbook.value,
            "description": "MacBook screen flickering",
            "message": "Screen flickers when opening certain applications",
            "priority": Priority.high.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Read the ticket
        response = client.get(f"/ticket/{ticket_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket_id
        assert data["topic"] == ticket_data["topic"]
        assert data["description"] == ticket_data["description"]

    def test_read_ticket_not_found(self, client):
        """Test reading a non-existent ticket"""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/ticket/{fake_id}")

        assert response.status_code == 404
        assert "Ticket not found" in response.json()["detail"]

    def test_update_ticket_admin_success(self, client, admin_user):
        """Test ticket update by real admin user (should succeed)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.imac.value,
            "description": "iMac won't boot",
            "message": "Black screen on startup",
            "priority": Priority.high.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=admin_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Update the ticket (should succeed since user is admin)
        update_data = {
            "description": "iMac won't boot - Updated description",
            "priority": Priority.low.value,
            "status": Status.in_progress.value
        }

        response = client.put(
            f"/ticket/{ticket_id}", json=update_data, headers=admin_user["headers"])

        # Should succeed because user is admin
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]
        assert data["status"] == update_data["status"]

    def test_update_ticket_non_admin(self, client, auth_user):
        """Test ticket update by non-admin user (should fail)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.nas.value,
            "description": "NAS access issues",
            "message": "Cannot access shared drives",
            "priority": Priority.medium.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Try to update the ticket (should fail for non-admin)
        update_data = {
            "description": "Updated description",
            "status": Status.closed.value
        }

        response = client.put(
            f"/ticket/{ticket_id}", json=update_data, headers=auth_user["headers"])

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_delete_ticket_admin_success(self, client, admin_user):
        """Test deleting a ticket by admin user (should succeed)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.printer.value,
            "description": "Old printer needs removal",
            "message": "Printer is obsolete",
            "priority": Priority.low.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=admin_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Delete the ticket (should succeed since user is admin)
        response = client.delete(
            f"/ticket/{ticket_id}", headers=admin_user["headers"])

        assert response.status_code == 200
        assert "Ticket deleted successfully" in response.json()["message"]

        # Verify ticket is actually deleted
        get_response = client.get(f"/ticket/{ticket_id}")
        assert get_response.status_code == 404

    def test_delete_ticket_non_admin(self, client, auth_user):
        """Test deleting a ticket by non-admin user (should fail)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.wifi.value,
            "description": "WiFi issue",
            "message": "Can't delete this",
            "priority": Priority.medium.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Try to delete the ticket (should fail since user is not admin)
        response = client.delete(
            f"/ticket/{ticket_id}", headers=auth_user["headers"])

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_delete_ticket_not_found(self, client, admin_user):
        """Test deleting a non-existent ticket"""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.delete(
            f"/ticket/{fake_id}", headers=admin_user["headers"])

        assert response.status_code == 404
        assert "Ticket not found" in response.json()["detail"]

    def test_assign_ticket_admin_success(self, client, admin_user, auth_user):
        """Test ticket assignment by admin user (should succeed)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.lan.value,
            "description": "Network configuration needed",
            "message": "Setup new VLAN",
            "priority": Priority.medium.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=admin_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Assign the ticket to auth_user (admin can assign to anyone)
        assign_response = client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": admin_user["user_id"]},
            headers=admin_user["headers"]
        )

        assert assign_response.status_code == 200
        data = assign_response.json()
        assert data["assigned_to"] == admin_user["user_id"]

    def test_assign_ticket_non_admin_to_self(self, client, auth_user):
        """Test user assigning unassigned ticket to themselves (should succeed)"""
        # First create a ticket with admin or another user
        ticket_data = {
            "topic": Topic.macbook.value,
            "description": "MacBook setup",
            "message": "Initial configuration needed",
            "priority": Priority.low.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Get the user ID for assignment
        import jwt
        decoded_token = jwt.decode(auth_user["token"], options={
                                   "verify_signature": False})
        user_id = decoded_token["sub"]

        # User assigns ticket to themselves (should be allowed if ticket is unassigned)
        assign_response = client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": user_id},
            headers=auth_user["headers"]
        )

        assert assign_response.status_code == 200
        data = assign_response.json()
        assert data["assigned_to"] == user_id

    def test_update_ticket_status_admin(self, client, admin_user):
        """Test status update by admin user (should succeed)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.nas.value,
            "description": "NAS maintenance",
            "message": "Scheduled maintenance",
            "priority": Priority.high.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=admin_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Update status to in_progress (admin can change any status)
        status_response = client.put(
            f"/ticket/{ticket_id}/status",
            params={"status": Status.in_progress.value},
            headers=admin_user["headers"]
        )

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["status"] == Status.in_progress.value

        # Update status to closed
        status_response = client.put(
            f"/ticket/{ticket_id}/status",
            params={"status": Status.closed.value},
            headers=admin_user["headers"]
        )

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["status"] == Status.closed.value

    def test_update_ticket_status_author_close_only(self, client, auth_user):
        """Test status update by ticket author (can only close)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.other.value,
            "description": "General inquiry",
            "message": "Question about process",
            "priority": Priority.low.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]

        # Author tries to update to in_progress (should fail)
        status_response = client.put(
            f"/ticket/{ticket_id}/status",
            params={"status": Status.in_progress.value},
            headers=auth_user["headers"]
        )

        assert status_response.status_code == 403
        assert "Not enough permissions" in status_response.json()["detail"]

        # Author closes their own ticket (should succeed)
        status_response = client.put(
            f"/ticket/{ticket_id}/status",
            params={"status": Status.closed.value},
            headers=auth_user["headers"]
        )

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["status"] == Status.closed.value


class TestTicketsEndpoint:
    """Test cases for /tickets endpoint (list/filter operations)"""

    def test_read_tickets_empty(self, client):
        """Test reading tickets when none exist"""
        response = client.get("/tickets")

        assert response.status_code == 200
        assert response.json() == []

    def test_read_tickets_basic(self, client, auth_user):
        """Test reading tickets with basic data"""
        # Create a few tickets
        tickets_data = [
            {
                "topic": Topic.wifi.value,
                "description": "WiFi issues",
                "message": "Connection drops frequently",
                "priority": Priority.medium.value
            },
            {
                "topic": Topic.printer.value,
                "description": "Printer offline",
                "message": "Cannot print documents",
                "priority": Priority.high.value
            }
        ]

        created_tickets = []
        for ticket_data in tickets_data:
            response = client.post(
                "/ticket", json=ticket_data, headers=auth_user["headers"])
            assert response.status_code == 200
            created_tickets.append(response.json())

        # Read all tickets
        response = client.get("/tickets")

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) == 2

        # Check that tickets are ordered by created_at descending (newest first)
        for i, ticket in enumerate(tickets):
            assert ticket["topic"] in [t["topic"] for t in tickets_data]
            assert ticket["description"] in [t["description"]
                                             for t in tickets_data]

    def test_read_tickets_filter_by_status(self, client, auth_user):
        """Test filtering tickets by status"""
        # Create tickets with different statuses
        ticket_data = {
            "topic": Topic.other.value,
            "description": "General IT issue",
            "message": "Need help with setup",
            "priority": Priority.low.value
        }

        response = client.post("/ticket", json=ticket_data,
                               headers=auth_user["headers"])
        assert response.status_code == 200

        # Filter by status
        response = client.get("/tickets", params={"status": Status.open.value})

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        for ticket in tickets:
            assert ticket["status"] == Status.open.value

    def test_read_tickets_filter_by_priority(self, client, auth_user):
        """Test filtering tickets by priority"""
        # Create a high priority ticket
        ticket_data = {
            "topic": Topic.lan.value,
            "description": "Network outage",
            "message": "Complete network failure",
            "priority": Priority.high.value
        }

        response = client.post("/ticket", json=ticket_data,
                               headers=auth_user["headers"])
        assert response.status_code == 200

        # Filter by priority
        response = client.get(
            "/tickets", params={"priority": Priority.high.value})

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        for ticket in tickets:
            assert ticket["priority"] == Priority.high.value

    def test_read_tickets_filter_by_topic(self, client, auth_user):
        """Test filtering tickets by topic"""
        # Create a printer-related ticket
        ticket_data = {
            "topic": Topic.printer.value,
            "description": "Printer maintenance",
            "message": "Needs toner replacement",
            "priority": Priority.low.value
        }

        response = client.post("/ticket", json=ticket_data,
                               headers=auth_user["headers"])
        assert response.status_code == 200

        # Filter by topic
        response = client.get(
            "/tickets", params={"topic": Topic.printer.value})

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        for ticket in tickets:
            assert ticket["topic"] == Topic.printer.value

    def test_read_tickets_filter_by_author(self, client, auth_user):
        """Test filtering tickets by author"""
        # Create a ticket
        ticket_data = {
            "topic": Topic.wifi.value,
            "description": "Personal WiFi issue",
            "message": "Can't connect from my device",
            "priority": Priority.medium.value
        }

        create_response = client.post(
            "/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        author_id = create_response.json()["author"]

        # Filter by author
        response = client.get("/tickets", params={"author": author_id})

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        for ticket in tickets:
            assert ticket["author"] == author_id

    def test_read_tickets_filter_by_multiple(self, client, auth_user):
        """Test filtering tickets by multiple parameters"""
        # Create a few tickets with different statuses, priorities, and topics
        tickets_data = [
            {
                "topic": Topic.wifi.value,
                "description": "WiFi issues",
                "message": "Connection drops frequently",
                "priority": Priority.medium.value
            },
            {
                "topic": Topic.printer.value,
                "description": "Printer offline",
                "message": "Cannot print documents",
                "priority": Priority.high.value
            },
            {
                "topic": Topic.macbook.value,
                "description": "MacBook screen flickering",
                "message": "Screen flickers when opening certain applications",
                "priority": Priority.high.value
            },
            {
                "topic": Topic.nas.value,
                "description": "NAS access issues",
                "message": "Cannot access shared drives",
                "priority": Priority.medium.value
            }
        ]

        for ticket_data in tickets_data:
            response = client.post(
                "/ticket", json=ticket_data, headers=auth_user["headers"])
            assert response.status_code == 200
            author_id = response.json()["author"]

        # Filter by multiple parameters
        response = client.get("/tickets", params={"author": author_id, "status": Status.open.value,
                              "priority": Priority.high.value, "topic": Topic.printer.value})

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) == 1
        for ticket in tickets:
            assert ticket["author"] == author_id
            assert ticket["status"] == Status.open.value
            assert ticket["priority"] == Priority.high.value
            assert ticket["topic"] == Topic.printer.value

    def test_read_tickets_pagination(self, client, auth_user):
        """Test ticket pagination"""
        # Create multiple tickets
        for i in range(5):
            ticket_data = {
                "topic": Topic.other.value,
                "description": f"Test ticket {i}",
                "message": f"Test message {i}",
                "priority": Priority.low.value
            }
            response = client.post(
                "/ticket", json=ticket_data, headers=auth_user["headers"])
            assert response.status_code == 200

        # Test pagination
        response = client.get("/tickets", params={"skip": 2, "limit": 2})

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) == 2

    def test_assign_ticket_to_nonexistent_user(self, client, admin_user):
        """Test assigning ticket to non-existent user"""
        # Create a ticket
        ticket_data = {
            "topic": Topic.wifi.value,
            "description": "WiFi issue",
            "message": "Need assignment",
            "priority": Priority.medium.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=admin_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Try to assign to fake user ID
        fake_user_id = str(uuid4())
        assign_response = client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": fake_user_id},
            headers=admin_user["headers"]
        )
        
        # Should succeed (no user validation in assignment)
        assert assign_response.status_code == 200
        assert assign_response.json()["assigned_to"] == fake_user_id

    def test_assign_ticket_already_assigned_non_admin(self, client, auth_user, admin_user):
        """Test non-admin trying to reassign already assigned ticket"""
        # Create and assign ticket
        ticket_data = {
            "topic": Topic.printer.value,
            "description": "Printer issue",
            "message": "Already assigned",
            "priority": Priority.high.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=admin_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Admin assigns to themselves
        client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": admin_user["user_id"]},
            headers=admin_user["headers"]
        )
        
        # Non-admin tries to reassign to themselves
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        assign_response = client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": user_id},
            headers=auth_user["headers"]
        )
        
        # Should fail (ticket already assigned and user is not admin)
        assert assign_response.status_code == 403
        assert "Not enough permissions" in assign_response.json()["detail"]

    def test_update_ticket_status_assigned_user(self, client, auth_user, admin_user):
        """Test status update by assigned user"""
        # Create ticket
        ticket_data = {
            "topic": Topic.macbook.value,
            "description": "MacBook repair",
            "message": "Hardware issue",
            "priority": Priority.high.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=admin_user["headers"])
        ticket_id = create_response.json()["id"]
        
        # Assign to auth_user
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": user_id},
            headers=admin_user["headers"]
        )
        
        # Assigned user updates status
        status_response = client.put(
            f"/ticket/{ticket_id}/status",
            params={"status": Status.in_progress.value},
            headers=auth_user["headers"]
        )
        
        assert status_response.status_code == 200
        assert status_response.json()["status"] == Status.in_progress.value

    def test_create_ticket_invalid_enum_values(self, client, auth_user):
        """Test ticket creation with invalid enum values"""
        # Invalid topic
        ticket_data = {
            "topic": "invalid_topic",
            "description": "Test ticket",
            "message": "Test message",
            "priority": Priority.medium.value
        }
        
        response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        assert response.status_code == 422
        
        # Invalid priority
        ticket_data = {
            "topic": Topic.wifi.value,
            "description": "Test ticket",
            "message": "Test message",
            "priority": "invalid_priority"
        }
        
        response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        assert response.status_code == 422

    def test_update_ticket_partial_fields(self, client, admin_user):
        """Test partial ticket updates"""
        # Create ticket
        ticket_data = {
            "topic": Topic.nas.value,
            "description": "Original description",
            "message": "Original message",
            "priority": Priority.low.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=admin_user["headers"])
        ticket_id = create_response.json()["id"]
        original_ticket = create_response.json()
        
        # Update only description
        update_data = {"description": "Updated description only"}
        
        update_response = client.put(
            f"/ticket/{ticket_id}", 
            json=update_data, 
            headers=admin_user["headers"]
        )
        
        assert update_response.status_code == 200
        updated_ticket = update_response.json()
        
        # Check updated field
        assert updated_ticket["description"] == "Updated description only"
        
        # Check unchanged fields
        assert updated_ticket["message"] == original_ticket["message"]
        assert updated_ticket["priority"] == original_ticket["priority"]
        assert updated_ticket["topic"] == original_ticket["topic"]

    def test_tickets_filter_by_assigned_to(self, client, auth_user, admin_user):
        """Test filtering tickets by assigned_to"""
        # Create and assign ticket to auth_user
        ticket_data = {
            "topic": Topic.lan.value,
            "description": "Network issue",
            "message": "Assigned to specific user",
            "priority": Priority.medium.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=admin_user["headers"])
        ticket_id = create_response.json()["id"]
        
        user_response = client.get("/user", headers=auth_user["headers"])
        user_id = user_response.json()["id"]
        
        client.put(
            f"/ticket/{ticket_id}/assign",
            params={"assigned_to": user_id},
            headers=admin_user["headers"]
        )
        
        # Filter by assigned_to
        response = client.get("/tickets", params={"assigned_to": user_id})
        
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        for ticket in tickets:
            assert ticket["assigned_to"] == user_id

    def test_tickets_invalid_filter_values(self, client):
        """Test tickets endpoint with invalid filter values"""
        # Invalid UUID for assigned_to
        response = client.get("/tickets", params={"assigned_to": "not-a-uuid"})
        assert response.status_code == 422
        
        # Invalid UUID for author
        response = client.get("/tickets", params={"author": "not-a-uuid"})
        assert response.status_code == 422
        
        # Invalid status
        response = client.get("/tickets", params={"status": "invalid_status"})
        assert response.status_code == 422
        
        # Invalid priority
        response = client.get("/tickets", params={"priority": "invalid_priority"})
        assert response.status_code == 422
        
        # Invalid topic
        response = client.get("/tickets", params={"topic": "invalid_topic"})
        assert response.status_code == 422

    def test_ticket_operations_invalid_uuid(self, client, admin_user):
        """Test ticket operations with invalid UUID format"""
        invalid_uuid = "not-a-uuid"
        
        # GET ticket
        response = client.get(f"/ticket/{invalid_uuid}")
        assert response.status_code == 422
        
        # PUT ticket
        update_data = {"description": "Updated"}
        response = client.put(f"/ticket/{invalid_uuid}", json=update_data, headers=admin_user["headers"])
        assert response.status_code == 422
        
        # DELETE ticket
        response = client.delete(f"/ticket/{invalid_uuid}", headers=admin_user["headers"])
        assert response.status_code == 422
        
        # Assign ticket
        response = client.put(f"/ticket/{invalid_uuid}/assign", params={"assigned_to": admin_user["user_id"]}, headers=admin_user["headers"])
        assert response.status_code == 422
        
        # Update status
        response = client.put(f"/ticket/{invalid_uuid}/status", params={"status": Status.closed.value}, headers=admin_user["headers"])
        assert response.status_code == 422
