from fastapi import FastAPI

from .core import database
from .models.base import Base
from .routes import auth, tickets, users, ai, history

# Create the database tables
Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Ticket System API",
    description="A REST API for managing IT support tickets",
    version="0.1.1",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Operations for authentication. The **register** and **token** endpoints allow you to register and login.",
        },
        {
            "name": "ticket",
            "description": "Operations for a single ticket. The **ticket** endpoint allows you to create, read, update and delete a ticket.",
        },
        {
            "name": "tickets",
            "description": "Operations for multiple tickets. The **tickets** endpoint allows you to read all tickets.",
        },
        {
            "name": "user",
            "description": "Operations for a single user. The **user** endpoint allows you to read, update and delete a user.",
        },
        {
            "name": "users",
            "description": "Operations for multiple users. The **users** endpoint allows you to read all users.",
        },
        {
            "name": "ai",
            "description": "Operations for ai purposes. The **ai** endpoint allows you to create requests to the ai.",
        },
        {
            "name": "history",
            "description": "Operations for ticket history. The **history** endpoints allow you to view ticket change history.",
        }
    ]
)

# Include routers
app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(ai.router)
app.include_router(history.router)
