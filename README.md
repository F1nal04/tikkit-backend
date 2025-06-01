![Version](https://img.shields.io/badge/version-0.0.11-blue.svg)

# Tikkit Backend

A comprehensive REST API for managing IT support tickets built with FastAPI and SQLAlchemy. Features user authentication, role-based access control, and AI-powered ticket assistance.

## Features

- 🎫 **Ticket Management**: Create, read, update, delete, and assign tickets
- 👥 **User Management**: User registration, authentication, and profile management
- 🔐 **Role-Based Access Control**: Admin, worker, user, and deactivated roles
- 🤖 **AI Integration**: AI-powered ticket solution suggestions
- 📊 **Advanced Filtering**: Filter tickets by status, priority, topic, assignee, and author
- 🔒 **Secure Authentication**: JWT tokens with Argon2 password hashing
- 📋 **Audit Trail**: Complete history tracking of all ticket changes

## Setup

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. **Clone the repository and navigate to the project directory**

2. **Create and activate a virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Optional, for AI features
```

5. **Run the application:**

```bash
fastapi dev app/main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Interactive API documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative API documentation (ReDoc)**: `http://localhost:8000/redoc`

## Data Models

### User Roles

- `admin` - Full access to all operations
- `worker` - Can be assigned tickets and update ticket status
- `user` - Can create tickets and close their own tickets
- `inactive` - Limited access
- `deactivated` - No access

### Ticket Status

- `open` - New ticket
- `in_progress` - Being worked on
- `closed` - Resolved
- `hold` - Temporarily paused

### Ticket Priority

- `low` - Non-urgent
- `medium` - Standard priority
- `high` - Urgent

### Ticket Topics

- `printer` - Printer issues
- `nas` - Network storage issues
- `wifi` - Wireless network issues
- `lan` - Wired network issues
- `macbook` - MacBook issues
- `imac` - iMac issues
- `other` - Other IT issues

### Change Types (History)

- `created` - Initial ticket creation
- `updated` - Field modifications
- `deleted` - Ticket deletion

## API Endpoints

### Authentication

- `POST /register` - Register a new user
- `POST /token` - Login and get access token

### Tickets

- `POST /ticket` - Create a new ticket (authenticated users)
- `GET /ticket/{ticket_id}` - Get a specific ticket
- `GET /ticket/{ticket_id}/with-history` - Get a ticket with complete change history
- `PUT /ticket/{ticket_id}` - Update a ticket (admin only)
- `DELETE /ticket/{ticket_id}` - Delete a ticket (admin only)
- `PUT /ticket/{ticket_id}/assign` - Assign ticket to user
- `PUT /ticket/{ticket_id}/status` - Update ticket status
- `GET /tickets` - List tickets with filtering options

### Ticket History

- `GET /ticket/{ticket_id}/history` - Get complete change history for a ticket

### Users

- `GET /user` - Get current user profile or specific user by query parameter
- `PUT /user/{user_id}` - Update user profile
- `DELETE /user/{user_id}` - Delete user (with ticket validation)
- `PUT /user/{user_id}/password` - Change user password
- `PUT /user/{user_id}/email` - Change user email
- `PUT /user/{user_id}/role` - Change user role (admin only)
- `GET /users` - List all users with filtering

### AI Integration

- `GET /ai_request/{ticket_id}` - Get AI-powered solution for a ticket (admin only)

## Permission System

### Ticket Operations

- **Create**: Any authenticated user
- **Read**: Any user (public access)
- **Update/Delete**: Admin only
- **Assign**: Admin or self-assignment to unassigned tickets
- **Status Update**: Admin, ticket author (close only), or assigned user

### User Operations

- **Profile Access**: Own profile or any profile (with optional auth)
- **Profile Update**: Own profile or admin for any profile
- **Password Change**: Own password (requires old password) or admin (no old password required)
- **Email Change**: Own email (requires password) or admin (no password required)
- **Role Change**: Admin only (cannot change admin roles)
- **Delete**: Admin only (prevents deletion if user has tickets)

## Security Features

- **JWT Authentication**: 30-minute token expiration with UTC timestamps
- **Argon2 Password Hashing**: Industry-standard password security
- **Role-Based Access Control**: Granular permissions based on user roles
- **Admin Protection**: Prevents modification of admin user roles
- **Data Integrity**: Prevents user deletion when tickets exist

## Development

### Running Tests

The project includes comprehensive integration tests covering all API endpoints and functionality.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py
pytest tests/test_tickets.py
pytest tests/test_user.py

# Run tests with coverage report
pytest --cov=app
```

### Test Suite Overview

The test suite consists of three main test files providing comprehensive coverage:

#### Authentication Tests (`tests/test_auth.py`)

- **Registration Tests**: User registration with validation, password strength, duplicate emails, field validation
- **Login Tests**: Authentication, wrong credentials, case sensitivity, long credential handling
- **Edge Cases**: Empty fields, null values, special characters in names, extremely long inputs
- **Security Tests**: Password complexity validation, email format validation

#### Ticket Management Tests (`tests/test_tickets.py`)

- **CRUD Operations**: Create, read, update, delete tickets with proper authentication
- **Role-Based Access**: Admin vs non-admin permissions for ticket modifications
- **Assignment System**: Ticket assignment workflows, self-assignment rules
- **Status Management**: Status updates by different user roles (admin, author, assignee)
- **Filtering & Pagination**: Filter tickets by status, priority, topic, author, assignee
- **Validation Tests**: Invalid enum values, malformed UUIDs, invalid filter parameters
- **Edge Cases**: Non-existent tickets, unauthorized operations, partial updates

#### User Management Tests (`tests/test_user.py`)

- **Profile Management**: Get user profiles, update user information, partial updates
- **Password Management**: Password changes with proper validation and admin overrides
- **Email Management**: Email updates with password verification
- **Role Management**: Admin-only role changes with protection for admin users
- **User Deletion**: Deletion validation with ticket dependency checks
- **User Listing**: User filtering by role with pagination support
- **Security Tests**: Unauthorized access prevention, invalid UUID handling

### Test Features

- **Comprehensive Coverage**: All endpoints and edge cases covered
- **Authentication Testing**: Proper JWT token handling and role-based access
- **Detailed Assertions**: Descriptive error messages for easy debugging
- **Database Isolation**: Each test uses a fresh database state
- **Fixture-Based Setup**: Reusable authenticated user fixtures
- **Validation Testing**: Input validation and error handling verification

### Example Test Command Usage

```bash
# Run auth tests only
pytest tests/test_auth.py -v

# Run ticket tests with specific pattern
pytest tests/test_tickets.py::TestTicketEndpoint::test_create_ticket_success -v

# Run user management tests
pytest tests/test_user.py -v

# Get test coverage report
pytest --cov=app --cov-report=html
```

### Database

The application uses SQLite by default with SQLAlchemy ORM. Database tables are created automatically on startup.

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Argon2**: Password hashing
- **PyJWT**: JSON Web Token implementation
- **OpenAI**: AI integration (optional)
- **Python-dotenv**: Environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## History Tracking

The system automatically tracks all changes made to tickets, providing a complete audit trail. History entries include:

- **Field Changes**: What field was modified (e.g., status, priority, description)
- **Old/New Values**: Previous and new values with user-friendly formatting
- **User Information**: Who made the change (with user names)
- **Timestamps**: When the change occurred (UTC)
- **Change Types**: Creation, updates, or deletion

### Tracked Fields

- Topic changes
- Description modifications
- Message updates
- Status changes
- Priority adjustments
- Assignment changes
- Ticket creation and deletion

### History Features

- **Automatic Tracking**: All changes are automatically recorded
- **User-Friendly Display**: User IDs are converted to names for readability
- **Chronological Order**: History entries are ordered newest first
- **Complete Audit Trail**: No changes go unrecorded
- **Persistent History**: History is preserved even after ticket deletion
