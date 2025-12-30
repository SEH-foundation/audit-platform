# Audit Platform

Clean microservices architecture for repository auditing.

## Architecture

```
audit-platform/
├── core/                    # Brain - Rules & Workflows
│   ├── workflows/          # YAML workflow definitions
│   ├── rules/              # Scoring rules
│   ├── knowledge/          # Metrics knowledge base
│   └── engine.py           # Workflow orchestrator
├── executors/              # Hands - Execution modules
│   ├── git-analyzer/       # Git operations
│   ├── static-analyzer/    # Code analysis
│   ├── security-scanner/   # Security scanning
│   ├── llm-reviewer/       # LLM-based review
│   └── report-generator/   # Report generation
├── gateway/                # API Layer
│   ├── mcp/               # MCP server for Claude
│   └── api/               # REST API for web
└── ui/                    # Web interface
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
export INFRA_ENV_PATH=/Users/maksymdemchenko/AI-Platform-ISO-main/infrastructure/.env
# Optional overrides:
export DATABASE_URL=postgres://user:pass@localhost:5432/audit
export REDIS_URL=redis://localhost:6379
```

### 3. Run MCP HTTP server

```bash
python -m gateway.mcp.http_server
# UI and MCP server available at http://localhost:8090
```

### 4. Run the API (optional)

```bash
python -m gateway.api.main
# API available at http://localhost:8080
```

### 5. Run CLI audit (optional)

```bash
python -m run --source /path/to/repo --task quick_scan
```

## Documentation

- `docs/GETTING_STARTED.md` - full setup and usage
- `docs/ESTIMATION_FORMULAS.md` - fixed formulas and where they are used
- `docs/MCP_WEB_SERVER.md` - MCP server details and UI

## Usage with Claude (MCP)

Add to your Claude config:

```json
{
  "mcpServers": {
    "audit-platform": {
      "command": "python",
      "args": ["-m", "gateway.mcp.server"],
      "cwd": "/path/to/audit-platform"
    }
  }
}
```

Then in Claude:
- "Audit the repository https://github.com/user/repo"
- "Explain what repo_health score means"
- "What level is this project and how to improve it?"

## Security Configuration (Recommended)

Set these environment variables for production deployments:

- `REQUIRE_AUTH=true` to enforce bearer token auth on MCP and API endpoints.
- `MCP_AUTH_TOKENS=token1,token2` to define allowed static tokens.
- `OAUTH_ALLOWED_CLIENT_IDS=...` to allow only known OAuth client IDs.
- `OAUTH_REDIRECT_DOMAINS=claude.ai,app.claude.ai` to restrict redirect hosts.
- `ALLOWED_ORIGINS=https://claude.ai,https://app.claude.ai,https://seh.foundation` for CORS.
- `ALLOWED_REPO_HOSTS=github.com,gitlab.com` to restrict repo cloning.
- `MCP_WORKSPACE_ROOT=/tmp/mcp_workspaces` to isolate cloned repos.
- `ENABLE_DANGEROUS_TOOLS=false` to disable `run_script`, `run_tests`, `check_lint`, `check_types`, `find_duplicates`.
- `MCP_TOOL_POLICY=production|internal|dev` to control safe vs privileged tools.
- `STRICT_ESTIMATION=true` to enforce validation bounds on estimates.
- `RATE_MIN`, `RATE_MAX`, `HOURS_PER_KLOC_MIN`, `HOURS_PER_KLOC_MAX` to override validation bounds.

Tool policy tiers:
- `production`: safe tools only
- `internal`: safe + privileged tools
- `dev`: all tools (still blocked by `ENABLE_DANGEROUS_TOOLS=false` unless explicitly enabled)

Dangerous tools (disabled by default):
- `run_script`, `run_tests`, `check_lint`, `check_types`, `find_duplicates`

Privileged tools (require `MCP_TOOL_POLICY=internal` or `dev`):
- `clone_repo`, `analyze_repo`, `scan_security`, `analyze_complexity`, `generate_report`, `export_results`, `batch_analyze`
- `upload_document`, `upload_document_file`, `get_document`, `delete_document`
- `update_settings`, `load_results`, `list_policies`

Renamed tool:
- `upload_document_file` (file_path based upload). This replaces the old `upload_document` file tool name.

## Available Tools (MCP)

See:
- `TOOLS.md` (policy tiers)
- `docs/MCP_WEB_SERVER.md` (HTTP MCP server usage)

## Report Chunking

The `generate_report` tool supports chunking for large outputs:

```json
{
  "name": "generate_report",
  "arguments": {
    "analysis_id": "abc123",
    "sections": ["summary", "metrics", "estimation"],
    "format": "markdown",
    "chunking": { "mode": "by_size", "max_chars": 20000 }
  }
}
```

## Scoring

### Repository Health (0-12)
- README (+2)
- License (+1)
- Tests (+2)
- CI/CD (+2)
- Docker (+1)
- Active commits (+2)
- Multiple contributors (+2)

### Technical Debt (0-15)
- Low complexity (+3)
- Low duplication (+3)
- Few lint issues (+3)
- Updated dependencies (+3)
- Good test coverage (+3)

### Product Levels

| Level | Health | Debt | Description |
|-------|--------|------|-------------|
| R&D Spike | 0-3 | 0-5 | Experimental |
| Prototype | 4-6 | 4-8 | Working demo |
| Internal Tool | 6-8 | 7-10 | Team-ready |
| Platform Module | 8-10 | 10-13 | Integration-ready |
| Near-Product | 10-12 | 12-15 | Production-ready |

## API Endpoints

### REST API (port 8080)

```
GET  /health                    # Health check
GET  /api/workflows             # List workflows
POST /api/audit                 # Start audit
GET  /api/audit/{id}            # Get status
GET  /api/audit/{id}/report     # Get report
WS   /api/ws/audit/{id}         # Progress updates
POST /api/explain/metric        # Explain metric
GET  /api/explain/level/{name}  # Explain level
POST /api/recommendations       # Get recommendations
```
