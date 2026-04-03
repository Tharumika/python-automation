def test_simulator_lists_supported_scenarios(client):
    response = client.get("/api/v1/simulator/scenarios")

    assert response.status_code == 200
    assert response.json() == {"scenarios": ["monitoring", "audit", "pubsub"]}


def test_simulator_creates_monitoring_event(client):
    response = client.post("/api/v1/simulator/events/monitoring")

    assert response.status_code == 202
    body = response.json()
    assert body["normalized_event"]["event_type"] == "google.cloud.monitoring.alert.v1.opened"
    assert body["matched_rule_names"] == ["Notify on GCP monitoring incidents"]


def test_simulator_rejects_unknown_scenario(client):
    response = client.post("/api/v1/simulator/events/not-real")

    assert response.status_code == 400
