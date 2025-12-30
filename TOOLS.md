# MCP Tools

This document lists all tools exposed by the audit platform and their default
policy tier. Actual availability depends on environment variables:
- `MCP_TOOL_POLICY=production|internal|dev`
- `ENABLE_DANGEROUS_TOOLS=true|false`

## Safe (production)

- `audit`
- `audit_preflight`
- `estimate_cocomo`
- `estimate_comprehensive`
- `estimate_methodology`
- `list_methodologies`
- `estimate_pert`
- `estimate_ai_efficiency`
- `calculate_roi`
- `get_regional_costs`
- `get_formulas`
- `get_constants`
- `explain_metric`
- `explain_product_level`
- `get_recommendations`
- `list_profiles`
- `list_contracts`
- `estimate_cost`
- `check_readiness`
- `check_compliance`
- `generate_document`
- `get_template_variables`
- `calculate_scores`
- `get_scoring_rubric`
- `store_memory`
- `recall_memory`
- `record_decision`
- `record_learning`
- `get_context`
- `validate_estimate`
- `get_settings`
- `estimate_custom`
- `compare_estimates`

## Privileged (internal/dev)

- `clone_repo`
- `analyze_repo`
- `scan_security`
- `analyze_complexity`
- `generate_report`
- `export_results`
- `batch_analyze`
- `upload_document` (content/text)
- `upload_document_file` (file_path)
- `get_document`
- `delete_document`
- `update_settings`
- `load_results`
- `list_policies`

## Dangerous (disabled by default)

- `run_script`
- `run_tests`
- `check_lint`
- `check_types`
- `find_duplicates`

## Notes
- `upload_document_file` is the file-based upload tool (PDF/DOCX).
- `upload_document` is the text/markdown upload tool.
