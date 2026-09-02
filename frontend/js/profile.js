import {
  getCompany,
  uploadArtifact,
  deleteArtifact,
  generateDocument,
} from "./api.js";
import {
  esc,
  completenessBadge,
  sourceBadge,
  formatSize,
  formatDate,
  showToast,
} from "./app.js";

export async function renderProfile(container, companyId) {
  container.innerHTML = `
    <div class="mb-3">
      <a href="#/" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-left me-1"></i>Back to companies
      </a>
    </div>
    <div id="profile-body" class="text-center text-secondary py-5">Loading…</div>`;

  const body = container.querySelector("#profile-body");
  let company;
  try {
    company = await getCompany(companyId);
  } catch (err) {
    body.innerHTML = `
      <div class="alert alert-danger mx-auto" style="max-width: 480px;">
        <i class="bi bi-exclamation-triangle me-2"></i>${esc(err.message)}
      </div>`;
    return;
  }

  body.innerHTML = `
    <div class="row g-4">
      <div class="col-lg-7">
        <div class="card mb-4">
          <div class="card-body">
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-2">
              <h2 class="h4 mb-0">${esc(company.name)}</h2>
              ${completenessBadge(company)}
            </div>
            <dl class="row profile-dl mb-0">
              ${detailRow("Industry", company.industry)}
              ${detailRow("Headquarters", company.hq_location)}
              ${detailRow("Website", websiteHtml(company.website))}
              ${detailRow("Contact email", mailHtml(company.contact_email))}
              ${detailRow("Contact phone", company.contact_phone)}
              ${detailRow("Description", company.description)}
            </dl>
          </div>
        </div>

        <div class="d-flex gap-2 flex-wrap">
          <a href="#/companies/${company.id}/edit" class="btn btn-outline-secondary">
            <i class="bi bi-pencil me-1"></i>Edit
          </a>
          <button id="generate-btn" class="btn btn-primary">
            <i class="bi bi-file-earmark-pdf me-1"></i>Generate summary
          </button>
        </div>
        <div id="generate-feedback" class="mt-3"></div>
      </div>

      <div class="col-lg-5">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="muted-label">Files &amp; artifacts</span>
            <span class="badge text-bg-light border">${company.artifacts_count}</span>
          </div>
          <div class="card-body">
            <form id="upload-form" class="d-flex gap-2 mb-3">
              <input type="file" id="upload-file" class="form-control form-control-sm" required>
              <button type="submit" class="btn btn-sm btn-outline-primary text-nowrap">
                <i class="bi bi-upload me-1"></i>Upload
              </button>
            </form>
            <div id="artifact-list" class="text-center text-secondary py-3">Loading…</div>
          </div>
        </div>
      </div>
    </div>`;

  const listEl = body.querySelector("#artifact-list");
  renderArtifacts(container, listEl, company.artifacts, company.id);

  body.querySelector("#upload-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = body.querySelector("#upload-file");
    const file = input.files && input.files[0];
    if (!file) return;
    const btn = e.target.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      await uploadArtifact(company.id, file);
      showToast("File uploaded");
      refreshProfile(container, company.id);
    } catch (err) {
      showToast(err.message, "danger");
      btn.disabled = false;
    }
  });

  body.querySelector("#generate-btn").addEventListener("click", async () => {
    const feedback = body.querySelector("#generate-feedback");
    const btn = body.querySelector("#generate-btn");
    btn.disabled = true;
    feedback.innerHTML = "";
    try {
      const result = await generateDocument(company.id);
      feedback.innerHTML = successAlert(result.message || "Document generated");
      showToast("Document generated");
      refreshProfile(container, company.id);
    } catch (err) {
      btn.disabled = false;
      if (err.status === 422 && err.body && err.body.success === false) {
        feedback.innerHTML = failureAlert(
          err.body.message || "Not enough information to generate a document"
        );
      } else {
        feedback.innerHTML = failureAlert(err.message);
      }
    }
  });
}

function detailRow(label, value) {
  const rendered = value == null || value === "" ? "<span class='text-secondary'>—</span>" : value;
  return `
    <dt class="col-sm-4 text-muted">${label}</dt>
    <dd class="col-sm-8">${rendered}</dd>`;
}

function websiteHtml(url) {
  if (!url) return "";
  const safe = esc(url);
  return `<a href="${safe}" target="_blank" rel="noopener">${safe}</a>`;
}

function mailHtml(email) {
  if (!email) return "";
  return `<a href="mailto:${esc(email)}">${esc(email)}</a>`;
}

function renderArtifacts(container, listEl, artifacts, companyId) {
  if (!artifacts || artifacts.length === 0) {
    listEl.innerHTML = `
      <i class="bi bi-folder2-open d-block fs-3 mb-2"></i>
      No files or artifacts yet.`;
    return;
  }

  const items = artifacts
    .map((a) => {
      const isPdf = (a.content_type || "").includes("pdf");
      const icon = isPdf ? "bi-file-earmark-pdf" : "bi-file-earmark";
      return `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
          <div class="d-flex align-items-center gap-2 overflow-hidden">
            <i class="bi ${icon} fs-5 text-secondary flex-shrink-0"></i>
            <div class="overflow-hidden">
              <div class="text-truncate" title="${esc(a.original_name)}">${esc(a.original_name)}</div>
              <div class="stat-muted">
                ${sourceBadge(a.source)} ${formatSize(a.size_bytes)}
                <span class="ms-1">${esc(formatDate(a.created_at))}</span>
              </div>
            </div>
          </div>
          <div class="d-flex gap-2 flex-shrink-0">
            <a class="btn btn-sm btn-outline-secondary" href="${esc(a.download_url)}" download>
              <i class="bi bi-download"></i><span class="visually-hidden">Download</span>
            </a>
            <button class="btn btn-sm btn-outline-danger delete-artifact" data-id="${a.id}">
              <i class="bi bi-trash"></i><span class="visually-hidden">Delete</span>
            </button>
          </div>
        </div>`;
    })
    .join("");

  listEl.innerHTML = items;

  listEl.querySelectorAll(".delete-artifact").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const name = btn.closest(".d-flex")?.querySelector(".text-truncate")?.textContent || "this item";
      if (!window.confirm(`Remove "${name}"?`)) return;
      try {
        await deleteArtifact(Number(btn.dataset.id));
        showToast("File removed");
        renderProfile(container, companyId);
      } catch (err) {
        showToast(err.message, "danger");
      }
    });
  });
}

function successAlert(message) {
  return `<div class="alert alert-success py-2 mb-0"><i class="bi bi-check-circle me-2"></i>${esc(message)}</div>`;
}

function failureAlert(message) {
  return `<div class="alert alert-warning py-2 mb-0"><i class="bi bi-exclamation-triangle me-2"></i>${esc(message)}</div>`;
}

function refreshProfile(container, companyId) {
  renderProfile(container, companyId);
}
