import connectors from "../../../data/connectors.json";

async function fetchWithTimeout(url, timeoutMs = 4000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const start = Date.now();
  try {
    const res = await fetch(url, { signal: controller.signal, cache: "no-store" });
    const latencyMs = Date.now() - start;
    return { ok: res.ok, status_code: res.status, latency_ms: latencyMs };
  } finally {
    clearTimeout(timeout);
  }
}

export async function GET() {
  const items = [];
  for (const connector of connectors) {
    const healthUrl = `${connector.url.replace(/\/$/, "")}/health`;
    try {
      const result = await fetchWithTimeout(healthUrl);
      items.push({
        id: connector.id,
        name: connector.name,
        url: connector.url,
        ok: result.ok,
        status_code: result.status_code,
        latency_ms: result.latency_ms,
        checked_at: new Date().toISOString(),
      });
    } catch (err) {
      items.push({
        id: connector.id,
        name: connector.name,
        url: connector.url,
        ok: false,
        status_code: null,
        latency_ms: null,
        checked_at: new Date().toISOString(),
      });
    }
  }

  return Response.json({ items });
}
