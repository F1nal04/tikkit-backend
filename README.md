# Tikkit Backend

A simple REST API for managing tickets built with FastAPI and SQLAlchemy.

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
fastapi dev app/main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## Available Endpoints

- `POST /ticket` - Create a new ticket
- `GET /tickets` - List all tickets
- `GET /ticket/{ticket_id}` - Get a specific ticket
- `PUT /ticket/{ticket_id}` - Update a ticket
- `DELETE /ticket/{ticket_id}` - Delete a ticket
