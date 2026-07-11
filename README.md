# Advanced Authentication System

This project implements a highly secure, scalable, and optimized authentication system built with **Django** and **Django REST Framework (DRF)**. The architecture is designed around RESTful principles, asynchronous task processing, distributed caching, and full containerization using Docker.

---

## 🚀 Key Features

- **Two-Step Registration:** Creates an initial user account in an inactive state, triggering a confirmation workflow. The account is fully activated only after verifying a valid One-Time Password (OTP).
- **Dual Login Mechanism:** Supports standard authentication via Username/Password (issuing JWT tokens) as well as quick login using Phone Number and a secure OTP.
- **Live OTP Security:** Generates cryptographically secure 6-digit verification codes with a strict 120-second expiration window managed completely in-memory.
- **Distributed Redis Architecture (Logical DBs):** Separates application data by allocating Redis Database `0` exclusively for Celery task queues and Database `1` for the central caching layer to prevent any data eviction conflicts.
- **Brute-Force & DoS Protection (Throttling):** Implements custom rate-limiting throttles across all sensitive endpoints (`otp_request`, `otp_verify`, login, etc.) to safeguard the infrastructure.
- **Comprehensive OpenAPI 3 Documentation:** Dynamically generates interactive documentation blueprints using `drf-spectacular`, properly splitting Request and Response components for an optimal frontend developer experience.

---

## 🛠 Tech Stack & Dependencies

| Component | Technology / Package | Purpose |
| :--- | :--- | :--- |
| **Core Framework** | Django 5.x & DRF | Main RESTful API development and request handling |
| **Database** | PostgreSQL 15 | Relational database handling primary application storage |
| **Task Queue** | Celery | Asynchronous background processing for sending OTP messages without blocking the client |
| **In-Memory Store** | Redis 7 (Alpine) | Acts as both the Celery message broker and the central distributed cache |
| **Authentication** | djangorestframework-simplejwt | Secure JWT-based token management (Access & Refresh tokens) |
| **Documentation** | drf-spectacular | Implements OpenAPI 3 schemas and automated UI rendering |

---

## 📦 Quick Start Guide (Docker)

The entire infrastructure—including the web server, relational database, in-memory cache, background worker, and database manager—is containerized and can be launched with a single command.

### 1. Environment Configuration
Create a `.env` file in the root directory of your project based on the template below:

```env
DB_NAME=your_db_name_here
DB_USER=your_db_user_here
DB_PASSWORD=your_db_password_here
DB_HOST=db
DB_PORT=5432

CELERY_REDIS_URL=redis://redis:6379/0
CACHE_REDIS_URL=redis://redis:6379/1

DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_DEBUG=True
```

### 2. Build and Run Containers
Execute the following command in your project terminal:
```
docker-compose up --build -d
```
### 3. Run Migrations & Create Superuser
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```