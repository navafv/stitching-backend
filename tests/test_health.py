"""
A simple smoke test for the project.
"""

from django.urls import reverse

def test_docs_schema(client):
    """
    Tests that the API schema endpoint is reachable.
    It's expected to return 200 (if public) or 401/403 (if protected),
    but not 404 or 500.
    """
    resp = client.get("/api/schema/")
    assert resp.status_code in (200, 401, 403)