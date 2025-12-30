"""
Contract Checker Executor
Checks compliance with contract requirements
"""
from typing import Any, Dict, Optional
from pathlib import Path
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseExecutor

logger = logging.getLogger(__name__)


# Sample contract templates (would be loaded from database in production)
CONTRACT_TEMPLATES = {
    "standard": {
        "name": "Standard Contract",
        "requirements": {
            "repo_health": {"min": 6, "description": "Basic repository hygiene"},
            "tech_debt": {"min": 8, "description": "Manageable technical debt"},
            "security_score": {"min": 1, "description": "No critical vulnerabilities"},
            "has_tests": {"value": True, "description": "Must have tests"},
            "has_ci": {"value": True, "description": "Must have CI/CD"},
        }
    },
    "enterprise": {
        "name": "Enterprise Contract",
        "requirements": {
            "repo_health": {"min": 10, "description": "High repository quality"},
            "tech_debt": {"min": 12, "description": "Low technical debt"},
            "security_score": {"min": 2, "description": "Strong security posture"},
            "has_tests": {"value": True, "description": "Must have tests"},
            "has_ci": {"value": True, "description": "Must have CI/CD"},
            "has_docker": {"value": True, "description": "Must be containerized"},
            "product_level": {"min": "Platform Module Candidate", "description": "Production-ready level"},
        }
    },
    "global_fund": {
        "name": "Global Fund R13",
        "requirements": {
            "repo_health": {"min": 8, "description": "Good documentation and practices"},
            "tech_debt": {"min": 10, "description": "Sustainable codebase"},
            "security_score": {"min": 2, "description": "Security audit passed"},
            "has_tests": {"value": True, "description": "Testing required"},
            "has_ci": {"value": True, "description": "Automated builds required"},
            "has_api_docs": {"value": True, "description": "API documentation required"},
        }
    },
    "minimal": {
        "name": "Minimal Requirements",
        "requirements": {
            "repo_health": {"min": 4, "description": "Basic organization"},
            "has_readme": {"value": True, "description": "Must have README"},
        }
    }
}

# Product level ordering for comparison
PRODUCT_LEVEL_ORDER = [
    "R&D Spike",
    "Prototype",
    "Internal Tool",
    "Platform Module Candidate",
    "Near-Product",
]


class ContractCheckerExecutor(BaseExecutor):
    """Executor for checking contract/policy compliance"""

    name = "contract-checker"

    async def run(self, action: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if action == "check":
            return await self.check(**inputs)
        elif action == "list_templates":
            return await self.list_templates()
        raise ValueError(f"Unknown action: {action}")

    async def check(
        self,
        quality: Optional[dict] = None,
        contract: Optional[dict] = None,
        policy: Optional[dict] = None,
        contract_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Check if project meets contract requirements.

        Args:
            quality: Quality analysis output (scores + structure + security)
            contract: Parsed contract (document-loader output)
            policy: Parsed policy (document-loader output)
            contract_id: Optional template ID fallback
        """
        quality = quality or {}
        structure = quality.get("structure", {})
        scores = {
            "repo_health": quality.get("repo_health", 0),
            "tech_debt": quality.get("tech_debt", 0),
            "security_score": quality.get("security_score", 0),
            "product_level": quality.get("product_level", "Unknown"),
        }

        contract_result = self._evaluate_document("contract", contract, scores, structure, contract_id)
        policy_result = self._evaluate_document("policy", policy, scores, structure, None)

        gaps = contract_result["gaps"] + policy_result["gaps"]
        required_fixes = contract_result["blockers"] + policy_result["blockers"]

        total_required = contract_result["required_total"] + policy_result["required_total"]
        met_required = contract_result["required_met"] + policy_result["required_met"]
        compliance_percent = round((met_required / total_required) * 100, 1) if total_required > 0 else 100

        return {
            "contract_compliant": contract_result["compliant"],
            "policy_compliant": policy_result["compliant"],
            "gaps": gaps,
            "required_fixes": required_fixes,
            "compliance_percent": compliance_percent,
        }

    async def list_templates(self) -> Dict[str, Any]:
        """List available contract templates"""
        return {
            "templates": [
                {
                    "id": template_id,
                    "name": template["name"],
                    "requirements_count": len(template["requirements"])
                }
                for template_id, template in CONTRACT_TEMPLATES.items()
            ]
        }

    def _get_actual_value(self, req_name: str, scores: dict, structure: dict) -> Any:
        """Get actual value for a requirement"""
        # Check in scores first
        if req_name in scores:
            return scores[req_name]

        # Check in structure
        if req_name in structure:
            return structure[req_name]

        # Special mappings
        mappings = {
            "has_readme": structure.get("has_readme", False),
            "has_tests": structure.get("has_tests", False),
            "has_ci": structure.get("has_ci", False),
            "has_docker": structure.get("has_docker", False),
            "has_api_docs": structure.get("has_api_docs", False),
        }

        return mappings.get(req_name, None)

    def _evaluate_document(
        self,
        source: str,
        doc: Optional[dict],
        scores: dict,
        structure: dict,
        fallback_template_id: Optional[str],
    ) -> Dict[str, Any]:
        """Evaluate a parsed contract/policy or fallback template."""
        if not doc and not fallback_template_id:
            return {
                "compliant": True,
                "gaps": [],
                "blockers": [],
                "required_total": 0,
                "required_met": 0,
            }

        requirements = []
        if doc and doc.get("requirements"):
            requirements = doc["requirements"]
        else:
            template = CONTRACT_TEMPLATES.get(fallback_template_id or "standard")
            for name, req in template["requirements"].items():
                requirement = {
                    "id": name,
                    "description": req.get("description", name),
                    "metric": name,
                    "threshold": req.get("min"),
                    "operator": ">=" if "min" in req else "==",
                    "priority": "required",
                }
                if "value" in req:
                    requirement["threshold"] = 1.0 if req["value"] else 0.0
                requirements.append(requirement)

        gaps = []
        blockers = []
        required_total = 0
        required_met = 0

        for req in requirements:
            metric = req.get("metric")
            threshold = req.get("threshold")
            operator = req.get("operator", ">=")
            priority = req.get("priority", "required")
            description = req.get("description", metric)

            if priority == "required":
                required_total += 1

            actual = self._get_actual_value(metric, scores, structure)
            if isinstance(actual, bool):
                actual_value = 1.0 if actual else 0.0
            else:
                actual_value = actual if actual is not None else 0.0

            satisfied = True
            if threshold is not None:
                if metric == "product_level" and isinstance(threshold, str):
                    satisfied = self._compare_product_levels(str(actual), threshold)
                else:
                    if operator == ">=":
                        satisfied = actual_value >= threshold
                    elif operator == "<=":
                        satisfied = actual_value <= threshold
                    elif operator == "==":
                        satisfied = actual_value == threshold
                    elif operator == ">":
                        satisfied = actual_value > threshold
                    elif operator == "<":
                        satisfied = actual_value < threshold

            if satisfied:
                if priority == "required":
                    required_met += 1
                continue

            gap = {
                "source": source,
                "requirement": req.get("id", metric),
                "metric": metric,
                "description": description,
                "required": threshold,
                "actual": actual_value,
                "operator": operator,
                "priority": priority,
            }
            gaps.append(gap)
            if priority == "required":
                blockers.append(f"{description}: expected {operator} {threshold}, got {actual_value}")

        compliant = required_total == required_met

        return {
            "compliant": compliant,
            "gaps": gaps,
            "blockers": blockers,
            "required_total": required_total,
            "required_met": required_met,
        }

    def _compare_product_levels(self, actual: str, required: str) -> bool:
        """Compare product levels"""
        try:
            actual_idx = PRODUCT_LEVEL_ORDER.index(actual)
            required_idx = PRODUCT_LEVEL_ORDER.index(required)
            return actual_idx >= required_idx
        except ValueError:
            return False

    def get_capabilities(self) -> list[str]:
        return ["check", "list_templates"]


def create_executor(config: Dict[str, Any] = None) -> ContractCheckerExecutor:
    return ContractCheckerExecutor(config)
