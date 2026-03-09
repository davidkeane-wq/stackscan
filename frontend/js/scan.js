const API_BASE = window.location.origin;

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function severityBadge(sev) {
  const map = {
    critical: "badge-critical",
    high:     "badge-failure",
    medium:   "badge-medium",
    low:      "badge-queued",
    info:     "badge-default",
  };
  return `<span class="badge ${map[sev] || "badge-default"}">${sev}</span>`;
}

// ── Severity ordering (most severe first) ───────────────────────────────────
const SEV_ORDER = ["critical", "high", "medium", "low", "info"];

function sevIndex(s) {
  const i = SEV_ORDER.indexOf(s);
  return i === -1 ? 99 : i;
}

// ── Build the page ──────────────────────────────────────────────────────────

function renderSummaryBar(findings) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  for (const f of findings) if (f.severity in counts) counts[f.severity]++;

  const bar = document.getElementById("summaryBar");
  const parts = SEV_ORDER
    .filter(s => counts[s] > 0)
    .map(s => `${severityBadge(s)} <span class="sev-count">${counts[s]}</span>`);

  if (parts.length === 0) {
    bar.innerHTML = '<span class="clean">No findings — Clean ✓</span>';
  } else {
    bar.innerHTML = parts.join(" ");
  }
  bar.style.display = "flex";
}

function renderFindings(findings) {
  const container = document.getElementById("findingsContainer");

  if (findings.length === 0) {
    container.innerHTML = '<p class="clean" style="font-size:1rem; margin-top:1rem">No findings ✓</p>';
    return;
  }

  // Group by scanner
  const byscanner = {};
  for (const f of findings) {
    if (!byscanner[f.scanner]) byscanner[f.scanner] = [];
    byscanner[f.scanner].push(f);
  }

  for (const [scanner, items] of Object.entries(byscanner)) {
    const sorted = [...items].sort((a, b) => sevIndex(a.severity) - sevIndex(b.severity));

    const section = document.createElement("section");
    section.className = "scanner-section";
    section.innerHTML = `<h2 class="scanner-heading">${scanner} <span class="scanner-count">${items.length}</span></h2>`;

    for (const f of sorted) {
      const fileLine = [f.file_path, f.line ? `line ${f.line}` : ""].filter(Boolean).join(" · ");
      const div = document.createElement("div");
      div.className = `finding finding-${f.severity}`;
      div.innerHTML = `
        <div class="finding-header">
          ${severityBadge(f.severity)}
          <span class="finding-category">${f.category}</span>
          <strong class="finding-title">${f.title}</strong>
        </div>
        ${fileLine ? `<div class="finding-file">${fileLine}</div>` : ""}
        <div class="finding-detail">${f.detail}</div>
      `;
      section.appendChild(div);
    }

    container.appendChild(section);
  }
}

async function loadScan() {
  const scanId = window.location.pathname.split("/").filter(Boolean).pop();
  if (!scanId) {
    document.getElementById("errorMsg").textContent = "No scan ID in URL.";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/v1/scans/${scanId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const scan = await res.json();

    document.title = `Scan – ${scan.repo || scanId} – StackScan`;
    document.getElementById("pageTitle").textContent =
      scan.repo ? `Scan: ${scan.repo}` : "Scan Report";

    const sha = scan.commit_sha ? scan.commit_sha.slice(0, 7) : "";
    document.getElementById("meta").innerHTML = [
      sha   ? `<code class="sha">${sha}</code>` : "",
      scan.timestamp ? `<span>${fmtDate(scan.timestamp)}</span>` : "",
      `<span class="scan-id-label">ID: <code>${scan.scan_id}</code></span>`,
    ].filter(Boolean).join(" · ");

    renderSummaryBar(scan.findings || []);
    renderFindings(scan.findings || []);
  } catch (e) {
    document.getElementById("errorMsg").textContent = `Failed to load scan: ${e.message}`;
  } finally {
    document.getElementById("loadSpinner").style.display = "none";
  }
}

loadScan();
