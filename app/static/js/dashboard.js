const body = document.body;
const apiPrefix = body.dataset.apiPrefix || "/api/v1";

const severityOrder = ["critical", "high", "medium", "info"];
const workflowOrder = ["simulated", "completed", "failed"];

document.getElementById("refresh-button")?.addEventListener("click", () => {
  loadDashboard();
});

document.querySelectorAll("[data-scenario]").forEach((button) => {
  button.addEventListener("click", async () => {
    const scenario = button.dataset.scenario;
    await triggerScenario(button, scenario);
  });
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
      <div class="card-meta">
        <span>${rule.event_type_filter || "all events"}</span>
        <span>${rule.severity_filter || "all severities"}</span>
      </div>
    `;
    container.appendChild(item);
  });
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
    renderRecentEvents(data.recent_events);
    renderWorkflowRuns(data.recent_workflow_runs);
    renderRules(data.rules);
  } catch (error) {
    document.getElementById("headline-text").textContent =
      "Dashboard data could not be loaded yet.";
    console.error(error);
  } finally {
    refreshButton?.removeAttribute("disabled");
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

loadDashboard();
