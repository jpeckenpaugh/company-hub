export class HttpError extends Error {
  constructor(status, detail, body) {
    super(detail || `Request failed (${status})`);
    this.status = status;
    this.detail = detail;
    this.body = body;
  }
}

const API_BASE = "/api";

async function http(path, options = {}) {
  const res = await fetch(path, options);
  if (res.status === 204) return null;

  const contentType = res.headers.get("content-type") || "";
  let body = null;
  if (contentType.includes("application/json")) {
    body = await res.json();
  }

  if (!res.ok) {
    let detail = body?.detail;
    if (detail == null && body?.message) detail = body.message;
    if (detail == null) detail = `Request failed (${res.status})`;
    throw new HttpError(res.status, detail, body);
  }
  return body;
}

export const listCompanies = (q) =>
  http(`${API_BASE}/companies${q ? `?q=${encodeURIComponent(q)}` : ""}`);

export const getCompany = (id) => http(`${API_BASE}/companies/${id}`);

export const createCompany = (data) =>
  http(`${API_BASE}/companies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export const updateCompany = (id, data) =>
  http(`${API_BASE}/companies/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export async function uploadArtifact(companyId, file) {
  const fd = new FormData();
  fd.append("file", file);
  return http(`${API_BASE}/companies/${companyId}/artifacts`, {
    method: "POST",
    body: fd,
  });
}

export const deleteArtifact = (id) =>
  http(`${API_BASE}/artifacts/${id}`, { method: "DELETE" });

export const generateDocument = (companyId) =>
  http(`${API_BASE}/companies/${companyId}/documents/generate`, {
    method: "POST",
  });
