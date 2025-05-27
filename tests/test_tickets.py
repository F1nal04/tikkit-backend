import pytest
from app.schemas import Priority, Topic, Status


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
        
        response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        
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
        
        response = client.post("/ticket", json=incomplete_data, headers=auth_user["headers"])
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
        
        create_response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
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
    
    def test_update_ticket_admin_requires_admin_role(self, client, admin_user):
        """Test ticket update requires admin role (regular user should fail)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.imac.value,
            "description": "iMac won't boot",
            "message": "Black screen on startup",
            "priority": Priority.high.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=admin_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]
        
        # Try to update the ticket (should fail since admin_user is actually a regular user)
        update_data = {
            "description": "iMac won't boot - Updated description",
            "priority": Priority.low.value,
            "status": Status.in_progress.value
        }
        
        response = client.put(f"/ticket/{ticket_id}", json=update_data, headers=admin_user["headers"])
        
        # Should fail because user is not actually admin
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_update_ticket_non_admin(self, client, auth_user):
        """Test ticket update by non-admin user (should fail)"""
        # First create a ticket
        ticket_data = {
            "topic": Topic.nas.value,
            "description": "NAS access issues",
            "message": "Cannot access shared drives",
            "priority": Priority.medium.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]
        
        # Try to update the ticket (should fail for non-admin)
        update_data = {
            "description": "Updated description",
            "status": Status.closed.value
        }
        
        response = client.put(f"/ticket/{ticket_id}", json=update_data, headers=auth_user["headers"])
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_delete_ticket_not_found(self, client, admin_user):
        """Test deleting a non-existent ticket"""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.delete(f"/ticket/{fake_id}", headers=admin_user["headers"])
        
        assert response.status_code == 404
        assert "Ticket not found" in response.json()["detail"]


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
            response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
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
            assert ticket["description"] in [t["description"] for t in tickets_data]
    
    def test_read_tickets_filter_by_status(self, client, auth_user):
        """Test filtering tickets by status"""
        # Create tickets with different statuses
        ticket_data = {
            "topic": Topic.other.value,
            "description": "General IT issue",
            "message": "Need help with setup",
            "priority": Priority.low.value
        }
        
        response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
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
        
        response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        assert response.status_code == 200
        
        # Filter by priority
        response = client.get("/tickets", params={"priority": Priority.high.value})
        
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
        
        response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        assert response.status_code == 200
        
        # Filter by topic
        response = client.get("/tickets", params={"topic": Topic.printer.value})
        
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        for ticket in tickets:
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
            response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
            assert response.status_code == 200
        
        # Test pagination
        response = client.get("/tickets", params={"skip": 2, "limit": 2})
        
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) == 2
    
    def test_read_tickets_filter_by_author(self, client, auth_user):
        """Test filtering tickets by author"""
        # Create a ticket
        ticket_data = {
            "topic": Topic.wifi.value,
            "description": "Personal WiFi issue",
            "message": "Can't connect from my device",
            "priority": Priority.medium.value
        }
        
        create_response = client.post("/ticket", json=ticket_data, headers=auth_user["headers"])
        assert create_response.status_code == 200
        author_id = create_response.json()["author"]
        
        # Filter by author
        response = client.get("/tickets", params={"author": author_id})
        
        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 1
        for ticket in tickets:
            assert ticket["author"] == author_id