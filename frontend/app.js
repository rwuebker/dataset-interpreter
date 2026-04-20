const defaultApiBase = "http://127.0.0.1:8011";
const configuredApiBase = window.localStorage.getItem("datasetInterpreterApiBase");
const apiBase = (configuredApiBase || defaultApiBase).replace(/\/+$/, "");

const dom = {
  apiBaseText: document.getElementById("apiBaseText"),
  createForm: document.getElementById("createForm"),
  competitionInput: document.getElementById("competitionInput"),
  datasetIdInput: document.getElementById("datasetIdInput"),
  createButton: document.getElementById("createButton"),
  errorText: document.getElementById("errorText"),
  dashboardRoot: document.getElementById("dashboardRoot"),
  statusValue: document.getElementById("statusValue"),
  stageValue: document.getElementById("stageValue"),
  progressValue: document.getElementById("progressValue"),
  jobIdValue: document.getElementById("jobIdValue"),
  stageHistoryList: document.getElementById("stageHistoryList"),
  summaryGrid: document.getElementById("summaryGrid"),
  nextStepsList: document.getElementById("nextStepsList"),
  qualityGrid: document.getElementById("qualityGrid"),
  artifactLinks: document.getElementById("artifactLinks"),
  featureTableBody: document.getElementById("featureTableBody"),
  featurePanel: document.getElementById("featurePanel"),
  featurePanelPlaceholder: document.getElementById("featurePanelPlaceholder"),
  featurePanelContent: document.getElementById("featurePanelContent"),
  closePanelButton: document.getElementById("closePanelButton"),
  cleaningGroups: document.getElementById("cleaningGroups"),
  applyCleaningButton: document.getElementById("applyCleaningButton"),
  applyCleaningHint: document.getElementById("applyCleaningHint"),
  jobJson: document.getElementById("jobJson"),
};

const state = {
  pollTimer: null,
  lastHydratedJobId: null,
  featureCards: [],
  selectedFeature: null,
  selectedCleaningStepIds: new Set(),
};

function normalizeCompetitionInput(rawValue) {
  const trimmed = (rawValue || "").trim();
  if (!trimmed) {
    return "";
  }

  const marker = "/competitions/";
  const markerIndex = trimmed.indexOf(marker);
  if (markerIndex === -1) {
    return trimmed;
  }

  const afterMarker = trimmed.slice(markerIndex + marker.length);
  const slug = afterMarker.split(/[/?#]/, 1)[0];
  return slug || trimmed;
}

function normalizeDatasetId(rawValue) {
  const trimmed = (rawValue || "").trim();
  if (!trimmed) {
    return "";
  }
  return trimmed
    .replace(/[^a-zA-Z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80);
}

function setError(message) {
  dom.errorText.textContent = message || "";
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    if (Number.isInteger(value)) {
      return value.toLocaleString();
    }
    return value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  }
  return String(value);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return `${Number(value).toFixed(2)}%`;
}

function utcToLocal(rawTimestamp) {
  if (!rawTimestamp) {
    return "-";
  }
  const date = new Date(rawTimestamp);
  if (Number.isNaN(date.getTime())) {
    return String(rawTimestamp);
  }
  return date.toLocaleString();
}

function renderPipelineStatus(jobPayload) {
  dom.dashboardRoot.classList.remove("hidden");
  dom.statusValue.textContent = formatValue(jobPayload.status);
  dom.stageValue.textContent = formatValue(jobPayload.current_stage);
  dom.progressValue.textContent = `${formatValue(jobPayload.progress)}%`;
  dom.jobIdValue.textContent = formatValue(jobPayload.job_id);

  const stageHistory = jobPayload.result?.pipeline_summary?.stage_history || [];
  dom.stageHistoryList.innerHTML = "";
  if (!stageHistory.length) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No stage history available yet.";
    dom.stageHistoryList.appendChild(li);
    return;
  }

  stageHistory.forEach((entry) => {
    const li = document.createElement("li");
    li.textContent = `${entry.stage || "stage"} · ${entry.status || "status"} · ${utcToLocal(entry.timestamp)}`;
    dom.stageHistoryList.appendChild(li);
  });
}

function renderExecutiveSummary(summaryPayload) {
  const summary = summaryPayload || {};
  const summaryItems = [
    ["Competition", summary.competition],
    ["Selected File", summary.selected_file],
    ["Rows", summary.rows],
    ["Columns", summary.columns],
    ["Problem Type", summary.inferred_problem_type],
    ["Target Column", summary.inferred_target_column],
    ["Readiness Label", summary.readiness_label],
    ["Readiness Score", summary.readiness_score],
  ];

  dom.summaryGrid.innerHTML = "";
  summaryItems.forEach(([label, value]) => {
    const item = document.createElement("article");
    item.className = "summary-item";
    item.innerHTML = `<strong>${label}</strong><span>${formatValue(value)}</span>`;
    dom.summaryGrid.appendChild(item);
  });

  dom.nextStepsList.innerHTML = "";
  const steps = summary.recommended_next_steps || [];
  if (!steps.length) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No recommended next steps returned.";
    dom.nextStepsList.appendChild(li);
    return;
  }
  steps.slice(0, 6).forEach((step) => {
    const li = document.createElement("li");
    li.textContent = String(step);
    dom.nextStepsList.appendChild(li);
  });
}

function renderDataQualityCards(jobPayload, summaryPayload) {
  const issues = jobPayload.result?.detected_issues || {};
  const cards = [
    ["Missing Data", issues.missing_data || "-"],
    ["Duplicates", issues.duplicates || "-"],
    ["Outliers", issues.outliers || "-"],
    ["Type Inconsistencies", issues.type_inconsistencies || "-"],
    ["Readiness Score", summaryPayload?.readiness_score ?? "-"],
  ];

  dom.qualityGrid.innerHTML = "";
  cards.forEach(([label, value]) => {
    const item = document.createElement("article");
    item.className = "stat";
    item.innerHTML = `<div class="label">${label}</div><div class="value">${formatValue(value)}</div>`;
    dom.qualityGrid.appendChild(item);
  });
}

function sortedArtifacts(manifestPayload, summaryPayload) {
  const preferredOrder = [
    "modeling_contract",
    "feature_cards",
    "cleaning_plan",
    "cleaning_receipt",
    "cleaned_train_csv",
    "manifest",
    "dataset_report",
    "data_profile",
    "issue_report",
    "interpretation",
  ];

  const mergedById = new Map();
  const fromManifest = manifestPayload?.artifacts || [];
  const fromSummary = summaryPayload?.artifacts || [];
  [...fromManifest, ...fromSummary].forEach((artifact) => {
    if (!artifact?.artifact_id) {
      return;
    }
    const existing = mergedById.get(artifact.artifact_id) || {};
    mergedById.set(artifact.artifact_id, { ...existing, ...artifact });
  });

  const artifacts = Array.from(mergedById.values());
  artifacts.sort((a, b) => {
    const aOrder = preferredOrder.indexOf(a.artifact_id);
    const bOrder = preferredOrder.indexOf(b.artifact_id);
    const rankA = aOrder === -1 ? 999 : aOrder;
    const rankB = bOrder === -1 ? 999 : bOrder;
    if (rankA !== rankB) {
      return rankA - rankB;
    }
    return String(a.artifact_id).localeCompare(String(b.artifact_id));
  });
  return artifacts;
}

function renderArtifactLinks(manifestPayload, summaryPayload) {
  const artifacts = sortedArtifacts(manifestPayload, summaryPayload);
  dom.artifactLinks.innerHTML = "";
  if (!artifacts.length) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No artifact links available.";
    dom.artifactLinks.appendChild(li);
    return;
  }

  artifacts.forEach((artifact) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = `${apiBase}${artifact.download_url}`;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = artifact.filename || `${artifact.artifact_id}.json`;

    const label = document.createElement("span");
    label.className = "muted";
    label.textContent = ` (${artifact.artifact_id})`;

    li.appendChild(link);
    li.appendChild(label);
    dom.artifactLinks.appendChild(li);
  });
}

function renderFeatureRows(featureCards) {
  dom.featureTableBody.innerHTML = "";
  state.featureCards = featureCards;
  state.selectedFeature = null;
  dom.featurePanelPlaceholder.classList.remove("hidden");
  dom.featurePanelContent.classList.add("hidden");
  dom.featurePanelContent.innerHTML = "";

  if (!featureCards.length) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="9" class="muted">No feature cards available.</td>';
    dom.featureTableBody.appendChild(row);
    return;
  }

  featureCards.forEach((card, index) => {
    const row = document.createElement("tr");
    row.className = "feature-row";
    row.dataset.featureIndex = String(index);
    row.innerHTML = `
      <td class="mono">${formatValue(card.column)}</td>
      <td>${formatValue(card.role)}</td>
      <td>${formatValue(card.physical_type)}</td>
      <td>${formatValue(card.semantic_type)}</td>
      <td>${formatPercent(card.missing_percent)}</td>
      <td>${formatValue(card.unique_count)}</td>
      <td><span class="pill">${formatValue(card.quality_status)}</span></td>
      <td>${formatValue(card.use_in_model)}</td>
      <td>${formatValue(card.recommended_action)}</td>
    `;
    row.addEventListener("click", () => openFeaturePanel(index));
    dom.featureTableBody.appendChild(row);
  });
}

function renderPanelItem(label, value) {
  const safeValue = formatValue(value);
  return `
    <article class="panel-item">
      <strong>${label}</strong>
      <div class="panel-value">${safeValue}</div>
    </article>
  `;
}

function buildHistogramChart(card) {
  const chart = card.chart || {};
  const bins = Array.isArray(chart.bins) ? chart.bins : [];
  const counts = Array.isArray(chart.counts) ? chart.counts : [];
  if (chart.type !== "histogram" || bins.length < 2 || counts.length < 1) {
    return null;
  }

  const maxCount = Math.max(...counts, 1);
  const rows = counts
    .map((count, index) => {
      const lower = bins[index];
      const upper = bins[index + 1];
      const label = `${formatValue(lower)} - ${formatValue(upper)}`;
      const pct = Math.max(2, Math.round((Number(count) / maxCount) * 100));
      return `
        <div class="chart-row">
          <span class="chart-label mono">${label}</span>
          <div class="chart-bar-wrap">
            <div class="chart-bar" style="width: ${pct}%"></div>
          </div>
          <span class="chart-count mono">${formatValue(count)}</span>
        </div>
      `;
    })
    .join("");

  return `<div class="chart-block">${rows}</div>`;
}

function buildCategoricalChart(card) {
  const chart = card.chart || {};
  let values = [];
  if (chart.type === "bar" && Array.isArray(chart.values)) {
    values = chart.values.map((item) => ({
      label: item?.label,
      count: Number(item?.count ?? 0),
    }));
  } else if (Array.isArray(card.top_values)) {
    values = card.top_values.map((item) => ({
      label: item?.value,
      count: Number(item?.count ?? 0),
    }));
  }

  const filtered = values.filter((item) => Number.isFinite(item.count) && item.count >= 0);
  if (!filtered.length) {
    return null;
  }

  const maxCount = Math.max(...filtered.map((item) => item.count), 1);
  const rows = filtered
    .map((item) => {
      const pct = Math.max(2, Math.round((item.count / maxCount) * 100));
      return `
        <div class="chart-row">
          <span class="chart-label mono">${formatValue(item.label)}</span>
          <div class="chart-bar-wrap">
            <div class="chart-bar" style="width: ${pct}%"></div>
          </div>
          <span class="chart-count mono">${formatValue(item.count)}</span>
        </div>
      `;
    })
    .join("");

  return `<div class="chart-block">${rows}</div>`;
}

function renderFeatureChart(card) {
  const histogram = buildHistogramChart(card);
  if (histogram) {
    return histogram;
  }

  const categorical = buildCategoricalChart(card);
  if (categorical) {
    return categorical;
  }

  return '<p class="muted">No chart data available.</p>';
}

function openFeaturePanel(index) {
  const card = state.featureCards[index];
  if (!card) {
    return;
  }
  state.selectedFeature = card.column;
  Array.from(dom.featureTableBody.querySelectorAll(".feature-row")).forEach((row) => {
    row.classList.toggle("selected", row.dataset.featureIndex === String(index));
  });

  const topValues = Array.isArray(card.top_values) ? card.top_values : [];
  const distribution = card.distribution || {};
  const topValuesHtml = topValues.length
    ? `<ul>${topValues
        .map((item) => `<li><span class="mono">${formatValue(item.value)}</span> · ${formatValue(item.count)}</li>`)
        .join("")}</ul>`
    : '<p class="muted">No top values available.</p>';

  const distributionEntries = Object.entries(distribution);
  const distributionHtml = distributionEntries.length
    ? `<ul>${distributionEntries
        .map(([key, value]) => `<li><span class="mono">${key}</span>: ${formatValue(value)}</li>`)
        .join("")}</ul>`
    : '<p class="muted">No numeric distribution available.</p>';
  const chartHtml = renderFeatureChart(card);

  dom.featurePanelPlaceholder.classList.add("hidden");
  dom.featurePanelContent.classList.remove("hidden");
  dom.featurePanelContent.innerHTML = `
    <div class="panel-grid">
      ${renderPanelItem("Column", card.column)}
      ${renderPanelItem("Role", card.role)}
      ${renderPanelItem("Physical Type", card.physical_type)}
      ${renderPanelItem("Semantic Type", card.semantic_type)}
      ${renderPanelItem("Missing Percent", formatPercent(card.missing_percent))}
      ${renderPanelItem("Unique Count", card.unique_count)}
      ${renderPanelItem("Unique Percent", formatPercent(card.unique_percent))}
      ${renderPanelItem("Quality Status", card.quality_status)}
      ${renderPanelItem("Use In Model", card.use_in_model)}
      ${renderPanelItem("Recommended Action", card.recommended_action)}
      ${renderPanelItem("Rationale", card.rationale)}
    </div>
    <div class="subsection">
      <h3>Chart</h3>
      ${chartHtml}
    </div>
    <div class="subsection">
      <h3>Top Values</h3>
      ${topValuesHtml}
    </div>
    <div class="subsection">
      <h3>Distribution</h3>
      ${distributionHtml}
    </div>
  `;
}

function closeFeaturePanel() {
  state.selectedFeature = null;
  Array.from(dom.featureTableBody.querySelectorAll(".feature-row")).forEach((row) => {
    row.classList.remove("selected");
  });
  dom.featurePanelPlaceholder.classList.remove("hidden");
  dom.featurePanelContent.classList.add("hidden");
  dom.featurePanelContent.innerHTML = "";
}

function cleaningGroupForOperation(operation) {
  if (operation === "set_as_target") {
    return "Target Setup";
  }
  if (operation === "exclude_column") {
    return "Exclude";
  }
  if (operation === "impute_missing") {
    return "Impute";
  }
  if (operation === "derive_indicator") {
    return "Derive";
  }
  if (operation === "outlier_treatment" || operation === "count_feature_treatment") {
    return "Outlier Handling";
  }
  return "Encoding / Other";
}

function updateApplyCleaningState() {
  const selectedCount = state.selectedCleaningStepIds.size;
  dom.applyCleaningButton.disabled = true;
  dom.applyCleaningHint.textContent = `${selectedCount} selected`;
}

function renderCleaningPlan(cleaningPlanPayload) {
  dom.cleaningGroups.innerHTML = "";
  const items = cleaningPlanPayload?.recommended_transformations || [];
  state.selectedCleaningStepIds = new Set();
  updateApplyCleaningState();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No cleaning transformations returned for this run.";
    dom.cleaningGroups.appendChild(empty);
    return;
  }

  const groups = new Map();
  items.forEach((step, index) => {
    const groupName = cleaningGroupForOperation(String(step.operation || ""));
    const key = `${String(step.operation || "unknown")}|${String(step.column || "dataset")}|${String(step.new_column || "")}|${index}`;
    if (!groups.has(groupName)) {
      groups.set(groupName, []);
    }
    groups.get(groupName).push({ step, index, key });
  });

  groups.forEach((entries, groupName) => {
    const section = document.createElement("section");
    section.className = "cleaning-group";

    const heading = document.createElement("h3");
    heading.textContent = groupName;
    section.appendChild(heading);

    const list = document.createElement("ul");
    list.className = "cleaning-group-list";

    entries.forEach(({ step, index, key }) => {
      const row = document.createElement("li");
      row.className = "cleaning-step";
      const label = document.createElement("label");
      label.className = "muted";

      const description = [
        step.column ? `column=${step.column}` : "column=dataset",
        step.operation ? `operation=${step.operation}` : "operation=unknown",
      ];
      if (step.strategy) {
        description.push(`strategy=${step.strategy}`);
      }

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = state.selectedCleaningStepIds.has(key);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          state.selectedCleaningStepIds.add(key);
        } else {
          state.selectedCleaningStepIds.delete(key);
        }
        updateApplyCleaningState();
      });

      const text = document.createElement("span");
      text.textContent = `${index + 1}. ${description.join(" · ")}`;

      label.appendChild(checkbox);
      label.appendChild(text);

      const meta = document.createElement("div");
      meta.className = "cleaning-step-meta";
      meta.textContent = step.rationale || "No rationale provided.";

      row.appendChild(label);
      row.appendChild(meta);
      list.appendChild(row);
    });

    section.appendChild(list);
    dom.cleaningGroups.appendChild(section);
  });
}

function renderRawJson(jobPayload) {
  dom.jobJson.textContent = JSON.stringify(jobPayload, null, 2);
}

function parseJsonl(text) {
  const rows = [];
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  lines.forEach((line, idx) => {
    try {
      rows.push(JSON.parse(line));
    } catch (error) {
      throw new Error(`Failed parsing feature_cards JSONL line ${idx + 1}.`);
    }
  });
  return rows;
}

async function fetchJson(path) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed ${response.status}: ${path}`);
  }
  return response.json();
}

async function fetchText(path) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed ${response.status}: ${path}`);
  }
  return response.text();
}

async function hydrateDashboard(jobId, jobPayload) {
  if (state.lastHydratedJobId === jobId) {
    return;
  }

  const requests = await Promise.allSettled([
    fetchJson(`/jobs/${jobId}/summary`),
    fetchJson(`/jobs/${jobId}/artifacts`),
    fetchText(`/jobs/${jobId}/artifacts/feature_cards`),
    fetchJson(`/jobs/${jobId}/artifacts/cleaning_plan`),
  ]);

  const summaryPayload = requests[0].status === "fulfilled" ? requests[0].value : jobPayload.result?.summary || {};
  const manifestPayload = requests[1].status === "fulfilled" ? requests[1].value : jobPayload.result?.artifact_manifest || {};
  const featureCards =
    requests[2].status === "fulfilled"
      ? parseJsonl(requests[2].value)
      : Array.isArray(jobPayload.result?.feature_cards)
        ? jobPayload.result.feature_cards
        : [];
  const cleaningPlanPayload = requests[3].status === "fulfilled" ? requests[3].value : {};

  renderExecutiveSummary(summaryPayload);
  renderDataQualityCards(jobPayload, summaryPayload);
  renderArtifactLinks(manifestPayload, summaryPayload);
  renderFeatureRows(featureCards);
  renderCleaningPlan(cleaningPlanPayload);
  renderRawJson(jobPayload);

  state.lastHydratedJobId = jobId;

  const failedCalls = requests.filter((entry) => entry.status === "rejected");
  if (failedCalls.length) {
    setError(
      `Loaded dashboard with partial data (${failedCalls.length} artifact endpoint${failedCalls.length > 1 ? "s" : ""} failed).`
    );
  }
}

async function pollJob(jobId) {
  const jobPayload = await fetchJson(`/jobs/${jobId}`);
  renderPipelineStatus(jobPayload);
  renderRawJson(jobPayload);

  if (jobPayload.status === "completed" || jobPayload.status === "failed") {
    if (state.pollTimer) {
      clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
    if (jobPayload.status === "completed") {
      await hydrateDashboard(jobId, jobPayload);
    }
  }
}

async function createJob(event) {
  event.preventDefault();
  setError("");
  closeFeaturePanel();

  const competitionSlug = normalizeCompetitionInput(dom.competitionInput.value);
  const datasetId = normalizeDatasetId(dom.datasetIdInput.value);
  if (!competitionSlug) {
    setError("Please enter a Kaggle competition slug or URL.");
    return;
  }

  dom.createButton.disabled = true;
  dom.createButton.textContent = "Creating...";
  state.lastHydratedJobId = null;

  try {
    const requestBody = {
      source_type: "kaggle",
      kaggle: { competition: competitionSlug },
    };
    if (datasetId) {
      requestBody.dataset_id = datasetId;
    }

    const response = await fetch(`${apiBase}/jobs/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    if (!response.ok) {
      throw new Error(`Job create failed (${response.status}): ${await response.text()}`);
    }

    const payload = await response.json();
    if (state.pollTimer) {
      clearInterval(state.pollTimer);
    }
    await pollJob(payload.job_id);
    state.pollTimer = setInterval(() => {
      void pollJob(payload.job_id).catch((error) => {
        setError(error instanceof Error ? error.message : "Failed to poll job status.");
      });
    }, 1500);
  } catch (error) {
    setError(error instanceof Error ? error.message : "Unknown error creating job.");
  } finally {
    dom.createButton.disabled = false;
    dom.createButton.textContent = "Create Job";
  }
}

dom.apiBaseText.textContent = apiBase;
dom.createForm.addEventListener("submit", createJob);
dom.closePanelButton.addEventListener("click", closeFeaturePanel);
