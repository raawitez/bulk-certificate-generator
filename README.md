# Bulk Certificate Generator API

A robust, asynchronous backend API that accepts bulk certificate generation requests (via JSON or CSV), queues them using a message broker, and generates professional PDF certificates in the background.

## 🏗️ Architecture

This project is built with separation of concerns and horizontal scalability in mind.

1. **FastAPI (API Gateway):** Handles incoming HTTP requests, validates payloads (Pydantic), creates database records, and publishes tasks to RabbitMQ. Returns a `202 Accepted` immediately so the client isn't blocked.
2. **RabbitMQ (Message Broker):** Decouples the API from the heavy PDF generation process. Configured for persistence (`durable=True`, `delivery_mode=2`) to guarantee tasks survive server restarts.
3. **Python Worker:** Consumes messages sequentially (`prefetch_count=1`), generates the PDFs in memory using `ReportLab`, and saves them via a Storage Abstraction layer. Updates the PostgreSQL state atomically.
4. **PostgreSQL:** The single source of truth for tracking Job and Certificate statuses.

## 🚀 Tech Stack

* **Language:** Python 3.11
* **Framework:** FastAPI
* **Database:** PostgreSQL (SQLAlchemy + async-compatible architecture)
* **Message Broker:** RabbitMQ
* **PDF Generation:** ReportLab
* **Testing:** Pytest (with SQLite in-memory DB and Mocking)
* **Infrastructure:** Docker & Docker Compose

## 🛠️ Setup & Installation

**1. Clone the repository and configure environment variables**
```bash
git clone [https://github.com/your-username/bulk-certificate-generator.git](https://github.com/your-username/bulk-certificate-generator.git)
cd bulk-certificate-generator
cp .env.example .env