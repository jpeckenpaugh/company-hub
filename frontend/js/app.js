import { renderList } from "./list.js";
import { renderProfile } from "./profile.js";
import { renderForm } from "./form.js";

const view = document.getElementById("view");

export function esc(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

export function completenessBadge(company) {
  if (company.is_complete) {
    return `<span class="badge rounded-pill badge-complete"><i class="bi bi-check-circle me-1"></i>Complete</span>`;
  }
  return `<span class="badge rounded-pill badge-incomplete"><i class="bi bi-exclamation-triangle me-1"></i>Incomplete</span>`;
}

export function sourceBadge(source) {
  const cls =
    source === "generated" ? "badge-source-generated" : "badge-source-upload";
  const label = source === "generated" ? "Generated" : "Uploaded";
  return `<span class="badge rounded-pill ${cls}">${label}</span>`;
}

export function formatSize(bytes) {
  if (bytes == null) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

export function showToast(message, type = "success") {
  const area = document.getElementById("toast-area");
  const icons = {
    success: "bi-check-circle-fill text-success",
    danger: "bi-exclamation-triangle-fill text-danger",
    warning: "bi-exclamation-circle-fill text-warning",
    info: "bi-info-circle-fill text-info",
  };
  const el = document.createElement("div");
  el.className = "toast align-items-center text-bg-light border-0";
  el.setAttribute("role", "status");
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="bi ${icons[type] || icons.info} me-2"></i>${esc(message)}
      </div>
      <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>`;
  area.appendChild(el);
  const toast = new bootstrap.Toast(el, { delay: 3500 });
  toast.show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
}

export function showViewLoading() {
  view.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-secondary" role="status">
        <span class="visually-hidden">Loading…</span>
      </div>
    </div>`;
}

function parseRoute(hash) {
  const path = (hash || "#/").replace(/^#/, "");
  const parts = path.split("/").filter(Boolean);
  if (parts.length === 0) return { name: "list" };
  if (parts[0] === "companies") {
    if (parts[1] === "new") return { name: "form", companyId: null };
    if (parts[1] && parts[2] === "edit")
      return { name: "form", companyId: Number(parts[1]) };
    if (parts[1]) return { name: "profile", companyId: Number(parts[1]) };
    return { name: "list" };
  }
  return { name: "list" };
}

function render(route) {
  showViewLoading();
  if (route.name === "profile") renderProfile(view, route.companyId);
  else if (route.name === "form") renderForm(view, route.companyId);
  else renderList(view);
}

export function navigate(hash) {
  window.location.hash = hash;
}

window.addEventListener("hashchange", () => render(parseRoute(location.hash)));
render(parseRoute(location.hash));
