"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function StatusView() {
  const [status, setStatus] = useState({ loading: true, items: [], error: null });

  useEffect(() => {
    let active = true;
    fetch("/api/status")
      .then((res) => res.json())
      .then((data) => {
        if (!active) return;
        setStatus({ loading: false, items: data.items || [], error: data.error || null });
      })
      .catch((err) => {
        if (!active) return;
        setStatus({ loading: false, items: [], error: err.message });
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">SEH Foundation</p>
          <h1>Connector Status</h1>
          <p className="subtitle">
            Live health checks for team connectors. Refresh the page to update.
          </p>
        </div>
        <Link className="btn btn-secondary" href="/">
          Back to Hub
        </Link>
      </header>

      <section className="section">
        {status.loading && <p>Checking connectors...</p>}
        {status.error && <p className="error">{status.error}</p>}
        <div className="grid">
          {status.items.map((item) => (
            <article className="card" key={item.id}>
              <div className="card-header">
                <h3>{item.name}</h3>
                <span className={`badge ${item.ok ? "production" : "dev"}`}>
                  {item.ok ? "healthy" : "down"}
                </span>
              </div>
              <p className="card-desc">{item.url}</p>
              <div className="meta">
                <div>
                  <span className="label">Status</span>
                  <span>{item.status_code || "n/a"}</span>
                </div>
                <div>
                  <span className="label">Latency</span>
                  <span>{item.latency_ms ? `${item.latency_ms} ms` : "n/a"}</span>
                </div>
                <div>
                  <span className="label">Checked</span>
                  <span>{item.checked_at}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
