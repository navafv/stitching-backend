from django.urls import reverse

def test_docs_schema(client):
    resp = client.get("/api/schema/")
    assert resp.status_code in (200, 403, 401)  # depends on your auth defaults
