# Getting Started

This guide explains how to run audit-platform locally and how to use it as an MCP
server for Claude or other clients.

## Prerequisites
- Python 3.10+
- pip
- (Optional) PostgreSQL and Redis for persistence

## Install
```bash
pip install -r requirements.txt
```

## Environment
The server reads environment variables in this order:
1) `INFRA_ENV_PATH` (loads a `.env` file first, if set)
2) Process environment

Recommended local setup:
```bash
export INFRA_ENV_PATH=/Users/maksymdemchenko/AI-Platform-ISO-main/infrastructure/.env
```

Optional overrides:
```bash
export DATABASE_URL=postgres://user:pass@localhost:5432/audit
export REDIS_URL=redis://localhost:6379
export SERVER_URL=http://localhost:8090
```

## Run MCP HTTP server (Web Claude)
```bash
python -m gateway.mcp.http_server
```
Open: `http://localhost:8090`

## Run REST API
```bash
python -m gateway.api.main
```
API: `http://localhost:8080`

## Run CLI Audit
```bash
python -m run --source /path/to/repo --task quick_scan
python -m run --source https://github.com/org/repo --task full_audit
```

## MCP Usage (Claude)
```json
{
  "mcpServers": {
    "audit-platform": {
      "command": "python",
      "args": ["-m", "gateway.mcp.server"],
      "cwd": "/Users/maksymdemchenko/audit-platform"
    }
  }
}
```

Typical flow:
1) `audit_preflight` (optional) -> get recommended task and questions
2) `audit` -> returns `analysis_id`
3) `generate_report` -> pass `analysis_id`

## Workflow Examples (EN)

### Preflight → Audit → Report
```json
{
  "name": "audit_preflight",
  "arguments": {
    "source": "https://github.com/org/repo",
    "goal": "quality",
    "region": "ua"
  }
}
```
Then run the recommended audit:
```json
{
  "name": "audit",
  "arguments": {
    "source": "https://github.com/org/repo",
    "task": "check_quality",
    "region": "ua"
  }
}
```
Finally, generate a report:
```json
{
  "name": "generate_report",
  "arguments": {
    "analysis_id": "abc123",
    "sections": ["summary", "metrics", "estimation"],
    "format": "markdown"
  }
}
```

### Full Audit
```json
{
  "name": "audit",
  "arguments": {
    "source": "/path/to/repo",
    "task": "full_audit",
    "region": "eu"
  }
}
```

## Приклади воркфлоу (UKR)

### Preflight → Audit → Report
```json
{
  "name": "audit_preflight",
  "arguments": {
    "source": "https://github.com/org/repo",
    "goal": "quality",
    "region": "ua"
  }
}
```
Потім запускаємо рекомендований аудит:
```json
{
  "name": "audit",
  "arguments": {
    "source": "https://github.com/org/repo",
    "task": "check_quality",
    "region": "ua"
  }
}
```
І фінально генеруємо звіт:
```json
{
  "name": "generate_report",
  "arguments": {
    "analysis_id": "abc123",
    "sections": ["summary", "metrics", "estimation"],
    "format": "markdown"
  }
}
```

### Повний аудит
```json
{
  "name": "audit",
  "arguments": {
    "source": "/path/to/repo",
    "task": "full_audit",
    "region": "eu"
  }
}
```

## Workspace Storage
Audit results are saved in a workspace folder (`MCP_WORKSPACE_ROOT`):
```
{MCP_WORKSPACE_ROOT}/{workspace_id}/
  .audit/
  analyses/{analysis_id}/
  reports/
  documents/
```

The `analysis_id` returned from `audit` is the key for reports and exports.
