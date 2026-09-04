// Browser interaction suite adapted from tmp/browser-interactions.mjs as node:test.
// Requires a live server (COMPANY_HUB_URL) and Chrome on :9222.
import { before, after, test } from "node:test";
import assert from "node:assert/strict";
import { connect, loginEvalJs } from "./cdp.mjs";

const BASE = process.env.COMPANY_HUB_URL || "http://127.0.0.1:8000";
const PW = process.env.COMPANY_HUB_ADMIN_PASSWORD || "test-admin-password";

let cdp;

before(async () => {
  cdp = await connect();
  await cdp.navigate(`${BASE}/`);
  await cdp.waitFor(`(document.body.innerText||'').toLowerCase().includes('sign in to continue')`);
  await cdp.evalJs(loginEvalJs(PW));
  await cdp.waitFor(`(document.body.innerText||'').toLowerCase().includes('add company')`);
});

after(() => {
  cdp.close();
});

test("country filter GB narrows list to HSBC/Shell", async () => {
  await cdp.waitFor(
    `!!document.getElementById('country-filter-slot') && !!document.getElementById('country-filter-slot').querySelector('.country-check')`
  );
  await cdp.evalJs(`
    (() => {
      const cb = document.getElementById('country-filter-slot').querySelector('[value="GB"]');
      cb.checked = true;
      cb.dispatchEvent(new Event('change', { bubbles: true }));
    })()
  `);
  assert.ok(
    await cdp.waitFor(
      `(document.body.innerText||'').includes('HSBC') && (document.body.innerText||'').includes('Shell') && !(document.body.innerText||'').includes('Toyota Motor')`
    )
  );
});

test("clearing filter restores full list", async () => {
  await cdp.evalJs(
    `document.getElementById('country-filter-slot').querySelector('#clear-countries').click()`
  );
  assert.ok(
    await cdp.waitFor(
      `(document.body.innerText||'').includes('Toyota Motor') && (document.body.innerText||'').includes('Carrefour')`
    )
  );
});

test("reference added via UI appears on profile", async () => {
  await cdp.evalJs("location.hash = '#/companies/1'");
  await cdp.waitFor(`!!document.getElementById('add-reference-btn')`);
  await cdp.evalJs(`
    (() => {
      document.getElementById('add-reference-btn').click();
      const f = document.getElementById('reference-form');
      f.elements['title'].value = 'Browser Smoke Ref';
      f.elements['url'].value = 'https://example.org/smoke';
      f.elements['description'].value = 'added via UI smoke';
      f.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    })()
  `);
  assert.ok(
    await cdp.waitFor(
      `(document.body.innerText||'').includes('Browser Smoke Ref') && (document.body.innerText||'').toLowerCase().includes('added by admin@localhost')`
    )
  );
});

test("reference removed via UI", async () => {
  await cdp.evalJs(`
    (() => {
      const btn = [...document.querySelectorAll('.remove-reference')].find((b) => b.parentElement.parentElement.innerText.includes('Browser Smoke Ref'));
      window.confirm = () => true;
      btn.click();
    })()
  `);
  assert.ok(
    await cdp.waitFor(`!(document.body.innerText||'').includes('Browser Smoke Ref')`)
  );
});

test("location added via UI appears on profile", async () => {
  await cdp.waitFor(`!!document.getElementById('add-location-btn')`);
  await cdp.evalJs(`
    (() => {
      document.getElementById('add-location-btn').click();
      const f = document.getElementById('location-form');
      f.elements['label'].value = 'Smoke Office';
      f.elements['city'].value = 'Berlin';
      f.elements['country'].value = 'DE';
      f.elements['type'].value = 'Office';
      f.elements['address'].value = '1 Smoke St';
      f.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    })()
  `);
  assert.ok(
    await cdp.waitFor(
      `(document.body.innerText||'').includes('Smoke Office') && (document.body.innerText||'').includes('Berlin')`
    )
  );
});

test("location removed via UI", async () => {
  await cdp.evalJs(`
    (() => {
      const btn = [...document.querySelectorAll('.remove-location')].find((b) => b.parentElement.parentElement.innerText.includes('Smoke Office'));
      window.confirm = () => true;
      btn.click();
    })()
  `);
  assert.ok(
    await cdp.waitFor(`!(document.body.innerText||'').includes('Smoke Office')`)
  );
});

test("industry renamed via UI", async () => {
  await cdp.evalJs("location.hash = '#/industries'");
  await cdp.waitFor(`!!document.querySelector('.rename-industry')`);
  await cdp.evalJs(`
    (() => {
      const row = [...document.querySelectorAll('.industry-row')].find((r) => r.innerText.includes('Energy'));
      row.querySelector('.rename-industry').click();
      const input = document.querySelector('.industry-edit-input');
      input.value = 'Energy Smoke';
      document.querySelector('.industry-edit-save').click();
    })()
  `);
  assert.ok(
    await cdp.waitFor(
      `(document.body.innerText||'').includes('Energy Smoke') && !(document.body.innerText||'').includes('\\nEnergy\\n')`
    )
  );
});

test("industry renamed back to Energy", async () => {
  await cdp.evalJs(`
    (() => {
      const row = [...document.querySelectorAll('.industry-row')].find((r) => r.innerText.includes('Energy Smoke'));
      row.querySelector('.rename-industry').click();
      const input = document.querySelector('.industry-edit-input');
      input.value = 'Energy';
      document.querySelector('.industry-edit-save').click();
    })()
  `);
  assert.ok(
    await cdp.waitFor(
      `(document.body.innerText||'').includes('Energy') && !(document.body.innerText||'').includes('Energy Smoke')`
    )
  );
});

test("company created via form with location lands on its profile", async () => {
  await cdp.evalJs("location.hash = '#/companies/new'");
  await cdp.waitFor(`!!document.getElementById('company-form')`);
  await cdp.evalJs(`
    (() => {
      const f = document.getElementById('company-form');
      f.elements['name'].value = 'UI Created Co';
      f.elements['website'].value = 'https://ui.example';
      f.elements['industry'].value = '1';
      document.getElementById('add-location-row').click();
      const row = document.querySelector('.location-row');
      row.querySelector('[data-field="label"]').value = 'HQ';
      row.querySelector('[data-field="city"]').value = 'London';
      row.querySelector('[data-field="country_code"]').value = 'GB';
      row.querySelector('[data-field="type"]').value = 'Headquarters';
      f.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    })()
  `);
  assert.ok(
    await cdp.waitFor(
      `location.hash.startsWith('#/companies/') && (document.body.innerText||'').includes('UI Created Co') && (document.body.innerText||'').includes('London')`
    )
  );
});