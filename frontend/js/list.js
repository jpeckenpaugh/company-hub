import { listCompanies } from "./api.js";
import { esc, completenessBadge, formatSize, showToast } from "./app.js";

export async function renderList(container) {
  container.innerHTML = `
    <div class="row mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Companies</h1>
      </div>
      <div class="col-auto">
        <a class="btn btn-primary" href="#/companies/new">
          <i class="bi bi-plus-lg me-1"></i>Add company
        </a>
      </div>
    </div>
    <div class="row mb-3">
      <div class="col-md-6 col-lg-4">
        <div class="input-group">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input type="search" id="company-search" class="form-control"
                 placeholder="Search by name…" aria-label="Search companies">
        </div>
      </div>
    </div>
    <div id="list-body" class="card">
      <div class="card-body text-center text-secondary py-4">Loading…</div>
    </div>`;

  const search = container.querySelector("#company-search");
  const body = container.querySelector("#list-body");
  let debounceTimer = null;

  async function load() {
    const q = search.value.trim();
    let companies;
    try {
      companies = await listCompanies(q);
    } catch (err) {
      body.innerHTML = `<div class="alert alert-danger m-3 mb-0">${esc(err.message)}</div>`;
      return;
    }
    body.innerHTML = renderTable(companies);
  }

  search.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(load, 250);
  });

  load();
}

function renderTable(companies) {
  if (companies.length === 0) {
    return `
      <div class="card-body text-center text-secondary py-5">
        <i class="bi bi-inbox d-block fs-2 mb-2"></i>
        No companies found.
      </div>`;
  }

  const rows = companies
    .map(
      (c) => `
      <tr class="company-row" data-id="${c.id}">
        <td>
          <a href="#/companies/${c.id}" class="fw-semibold text-decoration-none">${esc(c.name)}</a>
        </td>
        <td>${esc(c.industry) || '<span class="stat-muted">—</span>'}</td>
        <td>${esc(c.hq_location) || '<span class="stat-muted">—</span>'}</td>
        <td>
          <span class="stat-muted"><i class="bi bi-paperclip me-1"></i>${c.artifacts_count ?? 0}</span>
        </td>
        <td>${completenessBadge(c)}</td>
      </tr>`
    )
    .join("");

  return `
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Industry</th>
            <th scope="col">Headquarters</th>
            <th scope="col">Files</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}
