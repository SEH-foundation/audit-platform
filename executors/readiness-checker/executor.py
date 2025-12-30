"""
Readiness Checker Executor
Assesses whether a repository is ready for deeper analysis.
"""
from typing import Any, Dict, List
from pathlib import Path
import logging
import importlib.util

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseExecutor

logger = logging.getLogger(__name__)


class ReadinessCheckerExecutor(BaseExecutor):
    """Executor for repository readiness checks."""

    name = "readiness-checker"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._static = self._load_executor("static-analyzer", "static_analyzer")

    def _load_executor(self, folder_name: str, module_key: str):
        module_path = Path(__file__).parent.parent / folder_name / "executor.py"
        if not module_path.exists():
            raise FileNotFoundError(f"Executor module not found: {module_path}")
        spec = importlib.util.spec_from_file_location(module_key, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.create_executor(self.config)

    async def run(self, action: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if action == "check":
            return await self.check(**inputs)
        raise ValueError(f"Unknown action: {action}")

    async def check(self, path: str, scan: Dict[str, Any] = None, is_git: bool = False, **kwargs) -> Dict[str, Any]:
        """Assess readiness using repository structure signals."""
        structure = await self._static.analyze_structure(path)
        checks = self._build_checks(structure, is_git)

        total_points = sum(c["points"] for c in checks)
        earned_points = sum(c["points"] for c in checks if c["passed"])
        readiness_score = round((earned_points / max(total_points, 1)) * 100, 1)

        blockers = self._collect_blockers(checks)
        warnings = self._collect_warnings(checks)
        recommendations = self._collect_recommendations(checks)

        return {
            "is_ready": readiness_score >= 70 and not blockers,
            "readiness_score": readiness_score,
            "blockers": blockers,
            "warnings": warnings,
            "recommendations": recommendations,
            "can_proceed": readiness_score >= 50 and not blockers,
        }

    def _build_checks(self, structure: Dict[str, Any], is_git: bool) -> List[Dict[str, Any]]:
        return [
            {"id": "readme", "description": "README exists", "points": 10, "passed": structure.get("has_readme", False)},
            {"id": "readme_install", "description": "README has install steps", "points": 5, "passed": structure.get("readme_has_install", False)},
            {"id": "readme_usage", "description": "README has usage", "points": 5, "passed": structure.get("readme_has_usage", False)},
            {"id": "readme_substantive", "description": "README is substantive", "points": 5, "passed": structure.get("readme_size", 0) >= 400},
            {"id": "docs_folder", "description": "Docs folder present", "points": 5, "passed": structure.get("has_docs_folder", False)},
            {"id": "architecture_docs", "description": "Architecture docs present", "points": 5, "passed": structure.get("has_architecture_docs", False)},
            {"id": "dependency_files", "description": "Dependencies declared", "points": 10, "passed": len(structure.get("dependency_files", [])) > 0},
            {"id": "tests", "description": "Tests present", "points": 15, "passed": structure.get("has_tests", False)},
            {"id": "ci", "description": "CI configuration", "points": 7, "passed": structure.get("has_ci", False)},
            {"id": "docker", "description": "Docker configuration", "points": 6, "passed": structure.get("has_docker", False)},
            {"id": "api_docs", "description": "API documentation", "points": 4, "passed": structure.get("has_api_docs", False)},
            {"id": "changelog", "description": "Changelog present", "points": 5, "passed": structure.get("has_changelog", False)},
            {"id": "version_file", "description": "Version file present", "points": 4, "passed": structure.get("has_version_file", False)},
            {"id": "license", "description": "License present", "points": 6, "passed": structure.get("has_license", False)},
            {"id": "git_repo", "description": "Git history available", "points": 8, "passed": bool(is_git)},
        ]

    def _collect_blockers(self, checks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        blocker_ids = {"readme", "dependency_files", "tests", "ci"}
        blockers = []
        for check in checks:
            if check["id"] in blocker_ids and not check["passed"]:
                blockers.append({
                    "id": check["id"],
                    "description": check["description"],
                    "severity": "critical",
                })
        return blockers

    def _collect_warnings(self, checks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        warning_ids = {
            "readme_substantive",
            "docs_folder",
            "architecture_docs",
            "docker",
            "api_docs",
            "changelog",
            "version_file",
            "license",
        }
        warnings = []
        for check in checks:
            if check["id"] in warning_ids and not check["passed"]:
                warnings.append({
                    "id": check["id"],
                    "description": check["description"],
                })
        return warnings

    def _collect_recommendations(self, checks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        recommendations = []
        for check in checks:
            if not check["passed"]:
                recommendations.append({
                    "id": check["id"],
                    "action": f"Add: {check['description']}",
                    "impact": f"+{check['points']} points",
                })
        return recommendations[:10]


def create_executor(config: Dict[str, Any] = None) -> ReadinessCheckerExecutor:
    return ReadinessCheckerExecutor(config)
