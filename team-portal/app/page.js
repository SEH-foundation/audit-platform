import AuthBar from "./components/AuthBar";
import connectors from "../data/connectors.json";
import tools from "../data/tools.json";
import links from "../data/links.json";

export default function Home() {
  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">SEH Foundation</p>
          <h1>Connectors Hub</h1>
          <p className="subtitle">
            Internal catalog of MCP connectors, usage instructions, and trusted
            links. Keep this page updated for the whole team.
          </p>
        </div>
        <AuthBar />
      </header>

      <section className="section">
        <h2>Connectors</h2>
        <div className="grid">
          {connectors.map((connector) => (
            <article className="card" key={connector.id}>
              <div className="card-header">
                <h3>{connector.name}</h3>
                <span className={`badge ${connector.tier}`}>
                  {connector.tier}
                </span>
              </div>
              <p className="card-desc">{connector.description}</p>
              <div className="meta">
                <div>
                  <span className="label">URL</span>
                  <a href={connector.url} target="_blank" rel="noreferrer">
                    {connector.url}
                  </a>
                </div>
                {connector.download_url && (
                  <div>
                    <span className="label">Download</span>
                    <a href={connector.download_url} target="_blank" rel="noreferrer">
                      {connector.download_url}
                    </a>
                  </div>
                )}
                <div>
                  <span className="label">Owner</span>
                  <span>{connector.owner}</span>
                </div>
              </div>
              <div className="instructions">
                <span className="label">How to connect</span>
                <ol>
                  {connector.instructions.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </div>
              {tools[connector.id] && (
                <div className="tools">
                  <span className="label">Tools</span>
                  <div className="tool-groups">
                    {["safe", "privileged", "dangerous"].map((group) => (
                      <div className="tool-group" key={group}>
                        <div className={`tool-title ${group}`}>{group}</div>
                        <div className="tool-list">
                          {tools[connector.id][group].map((tool) => (
                            <span className="tool-chip" key={tool}>
                              {tool}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="tags">
                {connector.tags.map((tag) => (
                  <span className="tag" key={tag}>
                    {tag}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section split">
        <div>
          <h2>Quick Start</h2>
          <ol className="steps">
            <li>
              Go to <strong>Admin Settings → Connectors</strong> and add a
              connector URL.
            </li>
            <li>Set OAuth Client ID for the connector if required.</li>
            <li>
              Each team member connects it in <strong>Settings → Connectors</strong>.
            </li>
            <li>Enable only the tools you need per conversation.</li>
          </ol>
        </div>
        <div>
          <h2>Security Rules</h2>
          <ul className="rules">
            <li>Only use trusted connectors from official SEH sources.</li>
            <li>Disable tools that can write or execute code unless needed.</li>
            <li>Report suspicious tool behavior immediately.</li>
          </ul>
        </div>
      </section>

      <section className="section">
        <h2>Useful Links</h2>
        <div className="links">
          {links.map((link) => (
            <a className="link-card" href={link.url} key={link.url} target="_blank" rel="noreferrer">
              <div className="link-title">{link.title}</div>
              <div className="link-desc">{link.description}</div>
            </a>
          ))}
        </div>
      </section>

      <footer className="footer">
        Update connectors in <code>team-portal/data/connectors.json</code>.
      </footer>
    </main>
  );
}
