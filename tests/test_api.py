import io

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_auth_failure():
    from fastapi.testclient import TestClient
    from app.main import app
    unauth_client = TestClient(app)
    
    response = unauth_client.get("/api/jobs/some-id")
    assert response.status_code == 401
    assert "Missing X-API-Key header" in response.json()["detail"]

def test_create_job_json_success(client, mock_rabbitmq):
    payload = {
        "event_name": "Test Event",
        "event_date": "2026-01-01",
        "certificate_title": "Test Title",
        "recipients": [{"name": "John", "email": "john@test.com"}]
    }
    response = client.post("/api/jobs", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["total"] == 1
    
    assert mock_rabbitmq.called

def test_create_job_json_validation_error(client):
    payload = {
        "event_name": "Test Event",
        "event_date": "2026-01-01",
        "certificate_title": "Test Title",
        "recipients": [{"email": "not-an-email"}]
    }
    response = client.post("/api/jobs", json=payload)
    
    assert response.status_code == 422 # FastAPI Validation Error

def test_idempotency(client):
    payload = {
        "event_name": "Test Event",
        "event_date": "2026-01-01",
        "certificate_title": "Test Title",
        "recipients": [{"name": "John", "email": "john@test.com"}]
    }
    
    resp1 = client.post("/api/jobs", json=payload, headers={"Idempotency-Key": "test-key-123"})
    job_id_1 = resp1.json()["job_id"]
    
    resp2 = client.post("/api/jobs", json=payload, headers={"Idempotency-Key": "test-key-123"})
    job_id_2 = resp2.json()["job_id"]
    
    assert job_id_1 == job_id_2

def test_csv_upload_validation_failure(client):
    csv_content = b"name,email\nNo Email Person,\nBad Email Person,notanemail"
    
    response = client.post(
        "/api/jobs/csv",
        data={
            "event_name": "CSV Event",
            "event_date": "2026-01-01",
            "certificate_title": "CSV Title"
        },
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    )
    
    assert response.status_code == 400
    assert "Invalid CSV data found" in response.json()["detail"]["message"]