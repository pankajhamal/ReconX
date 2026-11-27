// All calls to the FastAPI backend.

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options) {
  const response = await fetch(API_URL + path, options);
  const data = await response.json();
  if (!response.ok) {
    // FastAPI puts the reason in "detail": either text or { errors: [...] }.
    const detail = data.detail;
    throw new Error(detail?.errors ? detail.errors.join("\n") : detail);
  }
  return data;
}

// kind is "internal" or "provider"
export function uploadFile(kind, file) {
  const form = new FormData();
  form.append("file", file);
  return request(`/uploads/${kind}`, { method: "POST", body: form });
}

export function runReconciliation() {
  return request("/reconciliation/run", { method: "POST" });
}

export function getBatches() {
  return request("/reconciliation/batches");
}

export function getSummary(batchId) {
  return request(`/reconciliation/batches/${batchId}/summary`);
}

export function getResults(batchId, filters) {
  // Leave out empty filters.
  const params = new URLSearchParams(
    Object.entries(filters).filter(([, value]) => value)
  );
  return request(`/reconciliation/batches/${batchId}/results?${params}`);
}

export function reportUrl(batchId) {
  return `${API_URL}/reconciliation/batches/${batchId}/report`;
}
