const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "https://loanprediction-api.onrender.com";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore JSON parse failure, keep statusText
    }
    throw new Error(detail);
  }

  return res.json();
}

export function getHealth() {
  return request("/health");
}

export function getModelInfo() {
  return request("/model-info");
}

export function predictLoan(application) {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify(application),
  });
}

export function predictBatch(applications) {
  return request("/predict/batch", {
    method: "POST",
    body: JSON.stringify({ applications }),
  });
}
