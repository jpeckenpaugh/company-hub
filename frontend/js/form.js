import { createCompany, updateCompany, getCompany } from "./api.js";
import { esc, showToast } from "./app.js";

const FIELDS = [
  ["name", "Name", "text", true],
  ["industry", "Industry", "text", false],
  ["hq_location", "Headquarters", "text", false],
  ["website", "Website", "url", false],
  ["contact_email", "Contact email", "email", false],
  ["contact_phone", "Contact phone", "text", false],
  ["description", "Description", "textarea", false],
];

export async function renderForm(container, companyId) {
  const editing = companyId != null;
  let company = null;
  if (editing) {
    try {
      company = await getCompany(companyId);
    } catch (err) {
      container.innerHTML = `
        <div class="alert alert-danger mx-auto" style="max-width: 560px;">
          <i class="bi bi-exclamation-triangle me-2"></i>${esc(err.message)}
        </div>`;
      return;
    }
  }

  const backHash = editing ? `#/companies/${companyId}` : "#/";
  container.innerHTML = `
    <div class="mb-3">
      <a href="${backHash}" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-left me-1"></i>Back
      </a>
    </div>
    <div class="card mx-auto" style="max-width: 640px;">
      <div class="card-body">
        <h1 class="h4 mb-4">${editing ? esc(`Edit ${company.name}`) : "Add company"}</h1>
        <form id="company-form" novalidate>
          <div id="form-alert"></div>
          ${FIELDS.map(fieldHtml).join("")}
          <div class="d-flex gap-2 mt-4">
            <button type="submit" class="btn btn-primary" id="save-btn">
              <i class="bi bi-check-lg me-1"></i>Save
            </button>
            <a href="${backHash}" class="btn btn-outline-secondary">Cancel</a>
          </div>
        </form>
      </div>
    </div>`;

  const form = container.querySelector("#company-form");
  const saveBtn = container.querySelector("#save-btn");
  const alertEl = container.querySelector("#form-alert");

  if (editing && company) {
    FIELDS.forEach(([name]) => {
      const input = form.elements[name];
      if (input) input.value = company[name] ?? "";
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    alertEl.innerHTML = "";
    const data = {};
    FIELDS.forEach(([name]) => {
      data[name] = form.elements[name].value.trim();
    });

    if (!data.name) {
      showFieldError(form, "name");
      return;
    }

    saveBtn.disabled = true;
    try {
      const saved = editing
        ? await updateCompany(companyId, data)
        : await createCompany(data);
      if (editing) {
        showToast("Company updated");
        window.location.hash = `#/companies/${saved.id}`;
      } else {
        showToast("Company added");
        window.location.hash = "#/";
      }
    } catch (err) {
      saveBtn.disabled = false;
      if (err.status === 422 && !data.name) {
        showFieldError(form, "name");
      } else {
        alertEl.innerHTML = `<div class="alert alert-danger py-2">${esc(err.message)}</div>`;
      }
    }
  });
}

function fieldHtml([name, label, type, required]) {
  const isTextarea = type === "textarea";
  const control = isTextarea
    ? `<textarea id="field-${name}" name="${name}" class="form-control" rows="3"></textarea>`
    : `<input type="${type}" id="field-${name}" name="${name}" class="form-control" ${required ? "required" : ""}>`;
  return `
    <div class="mb-3">
      <label for="field-${name}" class="form-label">
        ${label}${required ? ' <span class="text-danger">*</span>' : ""}
      </label>
      ${control}
    </div>`;
}

function showFieldError(form, name) {
  const input = form.elements[name];
  input.classList.add("is-invalid");
  input.setCustomValidity("Name is required");
  input.reportValidity();
  input.addEventListener(
    "input",
    () => {
      input.classList.remove("is-invalid");
      input.setCustomValidity("");
    },
    { once: true }
  );
}
