def test_event_detail_endpoint_returns_nested_payloads(client):
    ingest_response = client.post("/api/v1/simulator/events/monitoring")
    event_id = ingest_response.json()["normalized_event"]["id"]

    response = client.get(f"/api/v1/events/normalized/{event_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == event_id
    assert body["raw_event"]["id"]
    assert len(body["workflow_runs"]) == 1


def test_workflow_detail_endpoint_returns_rule_and_event(client):
    ingest_response = client.post("/api/v1/simulator/events/audit")
    workflow_id = ingest_response.json()["workflow_runs"][0]["id"]

    response = client.get(f"/api/v1/workflow-runs/{workflow_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == workflow_id
    assert body["normalized_event"]["event_type"] == "google.cloud.audit.log.v1.written"
    assert body["rule"]["name"] == "Escalate IAM or destructive audit changes"


def test_rule_create_and_toggle_flow(client):
    create_response = client.post(
        "/api/v1/rules",
        json={
            "name": "Notify on storage finalize",
            "description": "Demo rule from the control center stage.",
            "event_type_filter": "google.cloud.storage.object.v1.finalized",
            "severity_filter": "medium,high",
            "action_type": "notify",
            "action_target": "storage-ops",
            "priority": 55,
            "enabled": True,
        },
    )

    assert create_response.status_code == 201
    rule_id = create_response.json()["id"]

    toggle_response = client.patch(f"/api/v1/rules/{rule_id}", json={"enabled": False})

    assert toggle_response.status_code == 200
    assert toggle_response.json()["enabled"] is False

    get_response = client.get(f"/api/v1/rules/{rule_id}")

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Notify on storage finalize"
