def test_dashboard_page_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "GCP Cloud Ops Automation Hub" in response.text
    assert "Event Command Center" in response.text


def test_dashboard_summary_returns_expected_shape(client):
    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["headline"]
    assert body["total_raw_events"] == 0
    assert body["total_normalized_events"] == 0
    assert body["total_rules"] >= 1
    assert "severity_breakdown" in body
    assert "workflow_breakdown" in body
