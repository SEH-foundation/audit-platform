"""
Report Generator Executor
Generates audit reports in various formats
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseExecutor

logger = logging.getLogger(__name__)


class ReportGeneratorExecutor(BaseExecutor):
    """Executor for generating reports"""

    name = "report-generator"

    async def run(self, action: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate method"""
        if action == "generate":
            return await self.generate(**inputs)
        else:
            raise ValueError(f"Unknown action: {action}")

    async def generate(
        self,
        task: str = "",
        stages: dict = None,
        scores: dict = None,
        profile: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate full audit report"""
        stages = stages or {}
        scores = scores or {}

        # Generate markdown summary
        summary_md = self._generate_markdown(stages, scores, task)

        # Generate detailed JSON
        detailed_json = {
            "generated_at": datetime.now().isoformat(),
            "profile": profile,
            "task": task,
            "scores": scores,
            "stages": stages
        }

        # Generate executive summary
        executive_summary = self._generate_executive_summary(stages, scores)

        summary = executive_summary.get("one_liner", "")
        recommendations = self._collect_recommendations(stages)
        warnings = self._collect_warnings(stages)
        next_steps = self._collect_next_steps(stages)

        return {
            "summary_md": summary_md,
            "detailed_json": detailed_json,
            "executive_summary": executive_summary,
            "summary": summary,
            "recommendations": recommendations,
            "warnings": warnings,
            "next_steps": next_steps,
        }

    def _generate_markdown(self, stages: dict, scores: dict, task: str) -> str:
        """Generate markdown report"""
        quality = stages.get("quality_analysis", {})
        readiness_stage = stages.get("readiness_check", {})

        health = scores.get("repo_health", quality.get("repo_health", 0))
        debt = scores.get("tech_debt", quality.get("tech_debt", 0))
        security = scores.get("security_score", quality.get("security_score", 0))
        level = scores.get("product_level", quality.get("product_level", "Unknown"))
        readiness = scores.get("overall_readiness", quality.get("overall_readiness", readiness_stage.get("readiness_score", 0)))

        # Status emoji
        if readiness >= 80:
            emoji = "🚀"
            status = "Excellent"
        elif readiness >= 60:
            emoji = "✅"
            status = "Good"
        elif readiness >= 40:
            emoji = "⚠️"
            status = "Needs Improvement"
        else:
            emoji = "🔴"
            status = "Critical"

        structure = quality.get("structure", {}) or stages.get("quick_scan", {})
        git_history = quality.get("git_history", {}) or stages.get("load_source", {}).get("source_info", {})

        report = f"""# Repository Audit Report

{emoji} **Overall Status: {status}**

## Summary

| Metric | Score | Status |
|--------|-------|--------|
| Repository Health | {health}/12 | {self._score_status(health, 12)} |
| Technical Debt | {debt}/15 | {self._score_status(debt, 15)} |
| Security | {security}/3 | {self._score_status(security, 3)} |
| **Overall Readiness** | **{readiness}%** | |

**Product Level:** {level}
**Task:** {task or 'full_audit'}

## Repository Structure

- **Files:** {structure.get('file_count', 'N/A')}
- **Lines of Code:** {structure.get('loc', 'N/A')}
- **Languages:** {', '.join(structure.get('languages', ['Unknown']))}

### Checklist

| Feature | Status |
|---------|--------|
| README | {'✅' if structure.get('has_readme') else '❌'} |
| License | {'✅' if structure.get('has_license') else '❌'} |
| Tests | {'✅' if structure.get('has_tests') else '❌'} |
| CI/CD | {'✅' if structure.get('has_ci') else '❌'} |
| Docker | {'✅' if structure.get('has_docker') else '❌'} |

## Git History

- **Commits:** {git_history.get('commit_count', 'N/A')}
- **Contributors:** {git_history.get('contributors', 'N/A')}
- **Commit Frequency:** {git_history.get('commit_frequency', 'N/A')} commits/week
- **Branches:** {git_history.get('branch_count', 'N/A')}

"""

        # Add recommendations if available
        llm_review = stages.get("full_audit", {})
        if llm_review.get("recommendations"):
            report += "## Recommendations\n\n"
            for rec in llm_review["recommendations"]:
                report += f"- {rec}\n"
            report += "\n"

        # Add security findings
        security_data = quality.get("security", {})
        if security_data.get("vulnerability_count", 0) > 0:
            report += f"""## Security Findings

⚠️ Found {security_data.get('vulnerability_count', 0)} potential issues

- Critical: {security_data.get('critical_count', 0)}
- High: {security_data.get('high_count', 0)}
- Secrets exposed: {security_data.get('secrets_found', 0)}

"""

        report += f"""---

*Generated by Audit Platform on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        return report

    def _score_status(self, value: int, max_val: int) -> str:
        """Get status icon for score"""
        percent = (value / max_val) * 100 if max_val else 0
        if percent >= 80:
            return "🟢"
        elif percent >= 60:
            return "🟡"
        elif percent >= 40:
            return "🟠"
        return "🔴"

    def _generate_executive_summary(self, stages: dict, scores: dict) -> dict:
        """Generate executive summary for non-technical stakeholders"""
        quality = stages.get("quality_analysis", {})
        readiness_stage = stages.get("readiness_check", {})
        readiness = scores.get("overall_readiness", quality.get("overall_readiness", readiness_stage.get("readiness_score", 0)))
        level = scores.get("product_level", quality.get("product_level", "Unknown"))

        if readiness >= 80:
            status_emoji = "🚀"
            one_liner = "Project is production-ready with excellent quality metrics."
            recommendation = "proceed"
        elif readiness >= 60:
            status_emoji = "✅"
            one_liner = "Project is in good condition with minor improvements recommended."
            recommendation = "proceed_with_improvements"
        elif readiness >= 40:
            status_emoji = "⚠️"
            one_liner = "Project needs attention before production use."
            recommendation = "improve_first"
        else:
            status_emoji = "🔴"
            one_liner = "Project requires significant work before production use."
            recommendation = "major_rework"

        return {
            "status_emoji": status_emoji,
            "one_liner": one_liner,
            "product_level": level,
            "readiness_percent": readiness,
            "recommendation": recommendation,
            "key_metrics": {
                "health": f"{scores.get('repo_health', quality.get('repo_health', 0))}/12",
                "debt": f"{scores.get('tech_debt', quality.get('tech_debt', 0))}/15",
                "security": f"{scores.get('security_score', quality.get('security_score', 0))}/3"
            }
        }

    def get_capabilities(self) -> list[str]:
        return ["generate"]

    def _collect_recommendations(self, stages: dict) -> list:
        readiness = stages.get("readiness_check", {})
        audit = stages.get("full_audit", {})
        recs = []
        recs.extend(readiness.get("recommendations", []) or [])
        recs.extend(audit.get("recommendations", []) or [])
        return recs[:15]

    def _collect_warnings(self, stages: dict) -> list:
        readiness = stages.get("readiness_check", {})
        quality = stages.get("quality_analysis", {})
        warnings = []
        warnings.extend(readiness.get("warnings", []) or [])
        security = quality.get("security", {})
        if security.get("vulnerability_count", 0) > 0:
            warnings.append({
                "id": "security_findings",
                "description": f"Security findings: {security.get('vulnerability_count', 0)} issues",
            })
        return warnings

    def _collect_next_steps(self, stages: dict) -> list:
        readiness = stages.get("readiness_check", {})
        blockers = readiness.get("blockers", []) or []
        recommendations = readiness.get("recommendations", []) or []
        if blockers:
            return [f"Resolve blocker: {b.get('description', b.get('id', 'issue'))}" for b in blockers[:5]]
        return [f"Address: {r.get('action', r.get('id', 'recommendation'))}" for r in recommendations[:5]]


def create_executor(config: Dict[str, Any] = None) -> ReportGeneratorExecutor:
    return ReportGeneratorExecutor(config)
