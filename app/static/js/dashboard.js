const body = document.body;
const apiPrefix = body.dataset.apiPrefix || "/api/v1";

const severityOrder = ["critical", "high", "medium", "info"];
const workflowOrder = ["queued", "running", "simulated", "completed", "failed"];
const queueOrder = ["queued", "running", "completed", "failed"];

document.getElementById("refresh-button")?.addEventListener("click", () => {
  loadDashboard();
});

document.querySelectorAll("[data-scenario]").forEach((button) => {
  button.addEventListener("click", async () => {
    const scenario = button.dataset.scenario;
    await triggerScenario(button, scenario);
  });
});

document.getElementById("rule-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createRule();
});

document.getElementById("process-queue-button")?.addEventListener("click", async () => {
  await processQueue();
});

document.getElementById("test-notify-button")?.addEventListener("click", async () => {
  await runIntegrationTest("notify");
});

document.getElementById("test-incident-button")?.addEventListener("click", async () => {
  await runIntegrationTest("incident");
});

function formatLabel(value) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatTime(value) {
  if (!value) {
    return "n/a";
  }

  return new Date(value).toLocaleString();
}

function percent(value, total) {
  if (!total) {
    return 0;
  }

  return Math.max(6, Math.round((value / total) * 100));
}

function renderMeters(containerId, dataset, order, cssPrefix, total) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  order.forEach((key) => {
    const value = dataset[key] || 0;
    const meter = document.createElement("div");
    meter.className = "meter";
    meter.innerHTML = `
      <div class="meter-top">
        <strong>${formatLabel(key)}</strong>
        <span class="metric-value">${value}</span>
      </div>
      <div class="meter-bar">
        <div class="meter-fill fill-${cssPrefix === "workflow" ? key : key}" style="width: ${percent(value, total)}%"></div>
      </div>
    `;
    container.appendChild(meter);
  });
}

function renderRecentEvents(events) {
  const container = document.getElementById("recent-events");
  container.classList.remove("empty-state");
  container.innerHTML = "";

  if (!events.length) {
    container.classList.add("empty-state");
    container.textContent = "No normalized events yet. Send a test alert to see activity here.";
    return;
  }

  events.forEach((event) => {
    const item = document.createElement("article");
    item.className = "timeline-item";
    item.innerHTML = `
      <div class="timeline-dot severity-${event.severity}"></div>
      <div class="timeline-content">
        <div class="chip-row">
          <span class="severity-chip severity-${event.severity}">${event.severity}</span>
          <span class="rule-chip">${event.project_id}</span>
          ${event.resource_type ? `<span class="rule-chip">${event.resource_type}</span>` : ""}
        </div>
        <h3>${event.event_type}</h3>
        <p>${event.source}</p>
        <div class="timeline-meta">
          <span>${formatTime(event.occurred_at)}</span>
          <span>${event.resource_id || "resource n/a"}</span>
        </div>
      </div>
    `;
    item.addEventListener("click", () => inspectEvent(event.id, event.event_type));
    container.appendChild(item);
  });
}

function renderWorkflowRuns(runs) {
  const container = document.getElementById("workflow-list");
  container.classList.remove("empty-state");
  container.innerHTML = "";

  if (!runs.length) {
    container.classList.add("empty-state");
    container.textContent = "No workflow runs yet. Matching rules will show up here.";
    return;
  }

  runs.forEach((run) => {
    const item = document.createElement("article");
    item.className = "card-item";
    item.innerHTML = `
      <div class="chip-row">
        <span class="status-chip status-${run.status}">${run.status}</span>
        <span class="rule-chip">${run.action_type}</span>
        <span class="rule-chip">${run.dry_run ? "dry run" : "live"}</span>
      </div>
      <h3>Workflow ${run.id.slice(0, 8)}</h3>
      <div class="card-meta">
        <span>Started ${formatTime(run.started_at)}</span>
        <span>Rule ${run.rule_id.slice(0, 8)}</span>
      </div>
    `;
    item.addEventListener("click", () => inspectWorkflow(run.id));
    container.appendChild(item);
  });
}

function renderRules(rules) {
  const container = document.getElementById("rule-list");
  container.classList.remove("empty-state");
  container.innerHTML = "";

  if (!rules.length) {
    container.classList.add("empty-state");
    container.textContent = "No rules found.";
    return;
  }

  rules.forEach((rule) => {
    const item = document.createElement("article");
    item.className = "card-item";
    item.innerHTML = `
      <div class="chip-row">
        <span class="rule-chip">P${rule.priority}</span>
        <span class="rule-chip">${rule.action_type}</span>
        <span class="status-chip ${rule.enabled ? "status-completed" : "status-failed"}">
          ${rule.enabled ? "enabled" : "disabled"}
        </span>
      </div>
      <h3>${rule.name}</h3>
      <p>${rule.description || "No description set for this rule."}</p>
      <div class="card-meta">
        <span>${rule.event_type_filter || "all events"}</span>
        <span>${rule.severity_filter || "all severities"}</span>
        <span>${rule.action_target || "target n/a"}</span>
      </div>
      <div class="card-actions">
        <button class="secondary-button" data-inspect-rule="${rule.id}" type="button">Inspect</button>
        <button class="secondary-button" data-toggle-rule="${rule.id}" data-next-enabled="${rule.enabled ? "false" : "true"}" type="button">
          ${rule.enabled ? "Disable" : "Enable"}
        </button>
      </div>
    `;
    item.querySelector("[data-inspect-rule]")?.addEventListener("click", async (event) => {
      event.stopPropagation();
      await inspectRule(rule.id);
    });
    item.querySelector("[data-toggle-rule]")?.addEventListener("click", async (event) => {
      event.stopPropagation();
      const target = event.currentTarget;
      const enabled = target.dataset.nextEnabled === "true";
      await toggleRule(rule.id, enabled);
    });
    item.addEventListener("click", () => inspectRule(rule.id));
    container.appendChild(item);
  });
}

function renderIntegrationStatus(status) {
  const container = document.getElementById("integration-status-list");
  container.classList.remove("empty-state");
  container.innerHTML = "";

  const entries = [
    {
      label: "Slack Incoming Webhook",
      value: status.slack_configured ? `Configured -> ${status.slack_destination_label}` : "Not configured",
    },
    {
      label: "Notification Webhook",
      value: status.notification_webhook_configured ? "Configured" : "Not configured",
    },
    {
      label: "Incident Webhook",
      value: status.incident_webhook_configured ? "Configured" : "Not configured",
    },
    {
      label: "Execution Mode",
      value: status.mode,
    },
  ];

  entries.forEach((entry) => {
    const item = document.createElement("article");
    item.className = "card-item";
    item.innerHTML = `
      <div class="chip-row">
        <span class="rule-chip">${entry.label}</span>
      </div>
      <h3>${entry.value}</h3>
    `;
    container.appendChild(item);
  });

  document.getElementById("integration-mode-chip").textContent =
    status.dry_run ? "Dry Run Mode" : "Live Delivery Mode";
}

async function loadDashboard() {
  const refreshButton = document.getElementById("refresh-button");
  refreshButton?.setAttribute("disabled", "true");

  try {
    const response = await fetch("/dashboard/summary");
    if (!response.ok) {
      throw new Error(`Dashboard summary failed: ${response.status}`);
    }

    const data = await response.json();
    document.getElementById("headline-text").textContent = data.headline;
    document.getElementById("total-raw-events").textContent = data.total_raw_events;
    document.getElementById("total-normalized-events").textContent =
      data.total_normalized_events;
    document.getElementById("enabled-rules").textContent =
      `${data.enabled_rules} / ${data.total_rules}`;
    document.getElementById("total-workflow-runs").textContent = data.total_workflow_runs;
    document.getElementById("processing-mode").textContent = data.processing_mode;
    document.getElementById("queue-depth-label").textContent = `Queue depth: ${data.queue_depth}`;
    document.getElementById("mode-pill").textContent =
      (data.workflow_breakdown.completed || 0) > 0 ? "Mixed Mode" : "Dry Run";
    document.getElementById("last-sync").textContent = new Date().toLocaleTimeString();

    renderMeters(
      "severity-breakdown",
      data.severity_breakdown,
      severityOrder,
      "severity",
      data.total_normalized_events,
    );
    renderMeters(
      "workflow-breakdown",
      data.workflow_breakdown,
      workflowOrder,
      "workflow",
      data.total_workflow_runs,
    );
    renderMeters(
      "queue-breakdown",
      data.queue_breakdown,
      queueOrder,
      "workflow",
      Math.max(data.total_workflow_runs, data.queue_depth),
    );
    renderRecentEvents(data.recent_events);
    renderWorkflowRuns(data.recent_workflow_runs);
    renderRules(data.rules);
    await loadIntegrationStatus();
  } catch (error) {
    document.getElementById("headline-text").textContent =
      "Dashboard data could not be loaded yet.";
    console.error(error);
  } finally {
    refreshButton?.removeAttribute("disabled");
  }
}

async function loadIntegrationStatus() {
  try {
    const response = await fetch(`${apiPrefix}/integrations/status`);
    if (!response.ok) {
      throw new Error(`Integration status failed: ${response.status}`);
    }
    const data = await response.json();
    renderIntegrationStatus(data);
  } catch (error) {
    const container = document.getElementById("integration-status-list");
    container.classList.add("empty-state");
    container.textContent = "Integration status unavailable.";
    document.getElementById("integration-mode-chip").textContent = "Status unavailable";
  }
}

async function processQueue() {
  const feedback = document.getElementById("queue-feedback");
  const button = document.getElementById("process-queue-button");
  button?.setAttribute("disabled", "true");
  feedback.textContent = "Processing queued workflow jobs...";

  try {
    const response = await fetch(`${apiPrefix}/workflow-runs/process-queue?limit=20`, {
      method: "POST",
    });
    if (!response.ok) {
      throw new Error(`Queue processing failed: ${response.status}`);
    }
    const data = await response.json();
    feedback.textContent = `Processed ${data.processed_count} queued workflow job(s).`;
    await loadDashboard();
  } catch (error) {
    feedback.textContent = `Queue processing error: ${error.message}`;
  } finally {
    button?.removeAttribute("disabled");
  }
}

async function triggerScenario(button, scenario) {
  const feedback = document.getElementById("simulator-feedback");
  button.setAttribute("disabled", "true");
  feedback.textContent = `Injecting ${scenario} scenario...`;

  try {
    const response = await fetch(`${apiPrefix}/simulator/events/${scenario}`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`Simulator failed: ${response.status}`);
    }

    const data = await response.json();
    feedback.textContent =
      `Scenario created: ${data.normalized_event.event_type} -> ${data.workflow_runs.length} workflow run(s).`;
    await loadDashboard();
  } catch (error) {
    feedback.textContent = `Simulator error: ${error.message}`;
    console.error(error);
  } finally {
    button.removeAttribute("disabled");
  }
}

async function inspectEvent(eventId, eventType) {
  await loadInspector(`/api/v1/events/normalized/${eventId}`, `Event detail for ${eventType}`);
}

async function inspectWorkflow(workflowId) {
  await loadInspector(`/api/v1/workflow-runs/${workflowId}`, `Workflow detail for ${workflowId.slice(0, 8)}`);
}

async function inspectRule(ruleId) {
  await loadInspector(`/api/v1/rules/${ruleId}`, `Rule detail for ${ruleId.slice(0, 8)}`);
}

async function loadInspector(url, summary) {
  const summaryNode = document.getElementById("inspector-summary");
  const jsonNode = document.getElementById("inspector-json");
  summaryNode.textContent = `Loading: ${summary}`;
  jsonNode.textContent = "Loading...";

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Inspector failed: ${response.status}`);
    }
    const data = await response.json();
    if (data.result_payload?.connector_type) {
      summaryNode.textContent =
        `${summary} | ${data.result_payload.connector_type} -> ${data.result_payload.delivery}`;
    } else {
      summaryNode.textContent = summary;
    }
    jsonNode.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    summaryNode.textContent = "Inspector failed to load.";
    jsonNode.textContent = error.message;
  }
}

async function runIntegrationTest(testType) {
  const feedback = document.getElementById("integration-feedback");
  const buttonId = testType === "notify" ? "test-notify-button" : "test-incident-button";
  const button = document.getElementById(buttonId);
  button?.setAttribute("disabled", "true");
  feedback.textContent = `Sending ${testType} integration test through the queue...`;

  try {
    const response = await fetch(`${apiPrefix}/integrations/test/${testType}`, {
      method: "POST",
    });
    if (!response.ok) {
      throw new Error(`Integration test failed: ${response.status}`);
    }
    const data = await response.json();
    feedback.textContent =
      `Test ${data.test_type}: ${data.connector_type} -> ${data.delivery} (${data.workflow_status}).`;
    await loadDashboard();
    await inspectWorkflow(data.workflow_run_id);
  } catch (error) {
    feedback.textContent = `Integration test error: ${error.message}`;
  } finally {
    button?.removeAttribute("disabled");
  }
}

async function createRule() {
  const feedback = document.getElementById("rule-form-feedback");
  const form = document.getElementById("rule-form");
  const payload = {
    name: document.getElementById("rule-name").value.trim(),
    description: document.getElementById("rule-description").value.trim() || null,
    event_type_filter: document.getElementById("rule-event-type").value.trim() || null,
    severity_filter: document.getElementById("rule-severity").value.trim() || null,
    action_type: document.getElementById("rule-action-type").value,
    action_target: document.getElementById("rule-action-target").value.trim() || null,
    priority: Number(document.getElementById("rule-priority").value || 50),
    enabled: document.getElementById("rule-enabled").checked,
  };

  feedback.textContent = "Creating rule...";

  try {
    const response = await fetch(`${apiPrefix}/rules`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(errorBody || `Rule create failed: ${response.status}`);
    }
    const data = await response.json();
    feedback.textContent = `Rule created: ${data.name}`;
    form.reset();
    document.getElementById("rule-priority").value = 50;
    document.getElementById("rule-enabled").checked = true;
    await loadDashboard();
    await inspectRule(data.id);
  } catch (error) {
    feedback.textContent = `Rule create error: ${error.message}`;
  }
}

async function toggleRule(ruleId, enabled) {
  const feedback = document.getElementById("rule-form-feedback");
  feedback.textContent = `${enabled ? "Enabling" : "Disabling"} rule...`;

  try {
    const response = await fetch(`${apiPrefix}/rules/${ruleId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    if (!response.ok) {
      throw new Error(`Rule update failed: ${response.status}`);
    }
    const data = await response.json();
    feedback.textContent = `Rule updated: ${data.name} is now ${data.enabled ? "enabled" : "disabled"}.`;
    await loadDashboard();
    await inspectRule(data.id);
  } catch (error) {
    feedback.textContent = `Rule update error: ${error.message}`;
  }
}

loadDashboard();
