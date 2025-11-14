# Noor Stitching Institute - Backend

This is the complete Django backend for the Noor Stitching Institute management system. It provides a robust, scalable API to manage all aspects of the institute.

## Features

* **👤 Accounts & Roles**: Custom User model with Role-based permissions (Admin, Staff, Student).
* **🎓 Students & Enquiries**: Manages the full student lifecycle from initial enquiry to active student profile, including measurements.
* **📚 Courses & Batches**: Handles course curriculum, trainer profiles, batch scheduling, and student enrollments.
* **📅 Attendance**: Tracks daily student attendance per batch, with logic to automatically mark enrollments as "completed" upon meeting requirements.
* **💵 Finance**: Complete financial tracking, including:
    * Fee Receipts (with PDF generation)
    * Expense Tracking
    * Trainer Payroll Management
    * Inventory (Stock Items & Transactions)
    * Financial Analytics (Profit/Loss, etc.)
    * Outstanding Fee Reports
* **🪪 Certificates**: Issues, manages, and revokes student certificates. Includes automatic PDF generation and a public QR-code verification endpoint.
* **💬 Messaging**: A one-to-one chat system between students and the admin team, with read-status tracking.
* **🔔 Notifications**: A system for admins to send bulk notifications to all users, specific roles, or individual users.
* **🎉 Events**: A simple broadcast system for institute-wide events (e.g., holidays).
* **🔐 Authentication**: Secure JWT (JSON Web Token) authentication.
* **📄 API Documentation**: Automatic OpenAPI (Swagger/Redoc) schema generation.
* **🚀 Production Ready**: Configured with Gunicorn, Whitenoise, Sentry, and environment variables for production deployment.

## Tech Stack

* **Backend**: Django, Django REST Framework
* **Database**: PostgreSQL (Production), SQLite3 (Development)
* **Authentication**: djangorestframework-simplejwt (JWT)
* **API Docs**: drf-spectacular
* **PDF Generation**: xhtml2pdf
* **Deployment**: Docker, Gunicorn, Whitenoise
* **History Tracking**: django-simple-history

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/navafv/noor-backend.git](https://github.com/navafv/noor-backend.git)
    cd noor-backend
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Setup environment variables:**
    * Copy `.env.example` to a new file named `.env`.
    * Fill in the required values. A `DJANGO_SECRET_KEY` is mandatory.
    ```bash
    cp .env.example .env
    nano .env
    ```

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser (Admin):**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

The API will be available at `http://127.0.0.1:8000/`.
API documentation will be at `http://127.0.0.1:8000/api/docs/`.