const API_BASE = window.location.origin;

// ── Shared utilities ────────────────────────────────────────────────────────

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function badge(value) {
  if (!value) return '<span class="badge badge-default">—</span>';
  const cls = ["success","failure","cancelled","skipped","in_progress","queued"].includes(value)
    ? `badge-${value}` : "badge-default";
  return `<span class="badge ${cls}">${value.replace(/_/g, " ")}</span>`;
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

// ── Tab switching ───────────────────────────────────────────────────────────

function showTab(name) {
  document.getElementById("tab-scans").style.display     = name === "scans"     ? "block" : "none";
  document.getElementById("tab-pipelines").style.display = name === "pipelines" ? "block" : "none";
  document.querySelectorAll(".tab").forEach((t, i) => {
    t.classList.toggle("active", (name === "scans" && i === 0) || (name === "pipelines" && i === 1));
  });
}

// ── Scan list ───────────────────────────────────────────────────────────────

function countSeverities(findings) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  for (const f of findings) if (f.severity in counts) counts[f.severity]++;
  return counts;
}

function renderSeveritySummary(counts) {
  return Object.entries(counts)
    .filter(([, n]) => n > 0)
    .map(([sev, n]) => `${severityBadge(sev)} <span class="sev-count">${n}</span>`)
    .join(" ");
}

async function loadScans() {
  const msg  = document.getElementById("scansMessage");
  const list = document.getElementById("scansList");
  const spin = document.getElementById("scansSpinner");

  msg.textContent = "";
  msg.style.color = "";
  list.innerHTML  = "";
  spin.style.display = "inline-block";

  try {
    const res = await fetch(`${API_BASE}/api/v1/scans`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const scans = await res.json();

    if (scans.length === 0) {
      msg.textContent = "No scans yet. Run stackscan in your pipeline to create the first report.";
      return;
    }

    msg.textContent = `${scans.length} scan report(s)`;

    scans.forEach(scan => {
      const counts  = countSeverities(scan.findings || []);
      const sevHtml = renderSeveritySummary(counts);
      const total   = (scan.findings || []).length;
      const scanId  = scan.scan_id;
      const repo    = scan.repo || "unknown repo";
      const sha     = scan.commit_sha ? scan.commit_sha.slice(0, 7) : "";

      const card = document.createElement("div");
      card.className = "scan-card";
      card.innerHTML = `
        <div class="scan-card-header">
          <a href="/scans/${scanId}" class="scan-card-title">${repo}</a>
          <span class="scan-card-date">${fmtDate(scan.timestamp)}</span>
        </div>
        <div class="scan-card-meta">
          ${sha ? `<code class="sha">${sha}</code>` : ""}
          <span class="finding-count">${total} finding${total !== 1 ? "s" : ""}</span>
        </div>
        <div class="scan-card-severities">${sevHtml || '<span class="clean">Clean ✓</span>'}</div>
      `;
      list.appendChild(card);
    });
  } catch (e) {
    msg.style.color = "#f85149";
    msg.textContent = `Error loading scans: ${e.message}`;
  } finally {
    spin.style.display = "none";
  }
}

// ── Pipeline runs ───────────────────────────────────────────────────────────

async function fetchRuns() {
  const owner = document.getElementById("owner").value.trim();
  const repo  = document.getElementById("repo").value.trim();
  const msg   = document.getElementById("message");
  const table = document.getElementById("runsTable");
  const tbody = document.getElementById("runsBody");
  const btn   = document.getElementById("fetchBtn");
  const spin  = document.getElementById("spinner");

  if (!owner || !repo) {
    msg.className   = "error";
    msg.textContent = "Please enter both an owner and a repository name.";
    return;
  }

  msg.className = "";
  msg.textContent = "";
  table.style.display = "none";
  tbody.innerHTML = "";
  btn.disabled = true;
  spin.style.display = "inline-block";

  try {
    const res = await fetch(
      `${API_BASE}/api/pipelines/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    if (data.runs.length === 0) {
      msg.textContent = `No workflow runs found for ${owner}/${repo}.`;
      return;
    }
    msg.textContent = `Showing ${data.runs.length} of ${data.total_count} runs for ${owner}/${repo}.`;
    data.runs.forEach(run => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><a href="${run.html_url}" target="_blank" rel="noopener">${run.name}</a></td>
        <td>${badge(run.status)}</td>
        <td>${badge(run.conclusion)}</td>
        <td><code>${run.branch}</code></td>
        <td>${run.event}</td>
        <td>${fmtDate(run.created_at)}</td>
      `;
      tbody.appendChild(tr);
    });
    table.style.display = "table";
  } catch (e) {
    msg.className   = "error";
    msg.textContent = `Error: ${e.message}`;
  } finally {
    btn.disabled = false;
    spin.style.display = "none";
  }
}

["owner", "repo"].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("keydown", e => { if (e.key === "Enter") fetchRuns(); });
});
