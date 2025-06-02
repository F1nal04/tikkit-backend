# Tikkit Backend

[![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)](https://github.com/your-repo/tikkit-backend)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

> A modern REST API for IT support ticket management with AI-powered assistance

## ✨ Features

- 🎫 **Complete ticket lifecycle** - Create, assign, track, and resolve tickets
- 👥 **User management** - Registration, authentication, and role-based access
- 🤖 **AI assistance** - Get smart solution suggestions for tickets
- 📊 **Advanced filtering** - Search by status, priority, assignee, and more
- 🔒 **Secure by default** - JWT authentication with Argon2 password hashing
- 📋 **Full audit trail** - Track every change with detailed history

## 🚀 Quick Start

### 1. Install & Setup

```bash
# Clone and enter directory
git clone <repository-url>
cd tikkit-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key  # Optional for AI features
```

### 3. Run

```bash
fastapi dev app/main.py
```

🎉 **API ready at:** http://localhost:8000  
📚 **Documentation:** http://localhost:8000/docs

## 📖 API Overview

### Authentication

- `POST /register` - Create account
- `POST /token` - Login

### Tickets

- `POST /ticket` - Create ticket
- `GET /tickets` - List all tickets (with filters)
- `GET /ticket/{id}` - Get specific ticket
- `PUT /ticket/{id}` - Update ticket
- `PUT /ticket/{id}/assign` - Assign ticket
- `PUT /ticket/{id}/status` - Update status

### Users

- `GET /user` - Get profile
- `PUT /user/{id}` - Update profile
- `GET /users` - List users

### AI

- `GET /ai_request/{ticket_id}` - Get AI solution

## 🔐 User Roles

| Role          | Permissions                            |
| ------------- | -------------------------------------- |
| `admin`       | Full access to everything              |
| `worker`      | Can be assigned tickets, update status |
| `user`        | Create tickets, close own tickets      |
| `inactive`    | Limited access                         |
| `deactivated` | No access                              |

## 📝 Ticket Data

**Status:** `open` • `in_progress` • `closed` • `hold`  
**Priority:** `low` • `medium` • `high`  
**Topics:** `printer` • `nas` • `wifi` • `lan` • `macbook` • `imac` • `other`

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_tickets.py -v
```

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Default database
- **Argon2** - Password hashing
- **JWT** - Authentication tokens
- **OpenAI** - AI integration

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Need help?** Check the [full documentation](http://localhost:8000/docs) or [open an issue](https://github.com/your-repo/tikkit-backend/issues)
