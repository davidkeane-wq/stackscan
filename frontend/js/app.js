const API_BASE = window.location.origin;

// ── Tab switching ──────────────────────────────────────────────────────
function showTab(name) {
  document.getElementById('tab-pipelines').style.display = name === 'pipelines' ? 'block' : 'none';
  document.getElementById('tab-security').style.display  = name === 'security'  ? 'block' : 'none';
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', (name === 'pipelines' && i === 0) || (name === 'security' && i === 1));
  });
}

// ── Pipeline runs ──────────────────────────────────────────────────────
function badge(value) {
  if (!value) return '<span class="badge badge-default">—</span>';
  const cls = ["success","failure","cancelled","skipped","in_progress","queued"].includes(value)
    ? `badge-${value}` : "badge-default";
  return `<span class="badge ${cls}">${value.replace(/_/g, " ")}</span>`;
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

async function fetchRuns() {
  const owner = document.getElementById("owner").value.trim();
  const repo  = document.getElementById("repo").value.trim();
  const msg   = document.getElementById("message");
  const table = document.getElementById("runsTable");
  const tbody = document.getElementById("runsBody");
  const btn   = document.getElementById("fetchBtn");
  const spin  = document.getElementById("spinner");

  if (!owner || !repo) {
    msg.className = "error";
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
    const res = await fetch(`${API_BASE}/api/pipelines/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`);
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
    msg.className = "error";
    msg.textContent = `Error: ${e.message}`;
  } finally {
    btn.disabled = false;
    spin.style.display = "none";
  }
}

["owner","repo"].forEach(id => {
  document.getElementById(id).addEventListener("keydown", e => {
    if (e.key === "Enter") fetchRuns();
  });
});

// ── Security scan ──────────────────────────────────────────────────────
async function fetchLatestScan() {
  const msg     = document.getElementById("scanMessage");
  const results = document.getElementById("scanResults");
  const spin    = document.getElementById("scanSpinner");

  msg.textContent = "";
  results.innerHTML = "";
  spin.style.display = "inline-block";

  try {
    const res = await fetch(`${API_BASE}/api/scans/latest`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    msg.textContent = `Commit ${data.commit_sha.slice(0,7)} · Scanned ${fmtDate(data.scanned_at)} · ${data.summary}`;

    if (data.findings.length === 0) {
      results.innerHTML = '<p style="color:#3fb950">No issues found ✅</p>';
      return;
    }

    data.findings.forEach(f => {
      const icon = { critical: "🔴", warning: "🟡", info: "🟢" }[f.severity] || "⚪";
      const div = document.createElement("div");
      div.className = "finding";
      div.innerHTML = `
        <div class="finding-header">${icon} <strong>${f.severity.toUpperCase()}</strong> — ${f.category}</div>
        <div class="finding-file">${f.file}</div>
        <div>${f.issue}</div>
        <div class="finding-recommendation">💡 ${f.recommendation}</div>
      `;
      results.appendChild(div);
    });
  } catch (e) {
    msg.style.color = "#f85149";
    msg.textContent = `Error: ${e.message}`;
  } finally {
    spin.style.display = "none";
  }
}
