"""
Quality Analyzer Executor
Aggregates structure, dependency, security, and scoring signals.
"""
from typing import Any, Dict
from pathlib import Path
import logging
import importlib.util

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseExecutor

logger = logging.getLogger(__name__)


class QualityAnalyzerExecutor(BaseExecutor):
    """Executor for combined quality analysis."""

    name = "quality-analyzer"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._static = self._load_executor("static-analyzer", "static_analyzer")
        self._security = self._load_executor("security-scanner", "security_scanner")
        self._git = self._load_executor("git-analyzer", "git_analyzer")
        self._scoring = self._load_executor("scoring-engine", "scoring_engine")

    def _load_executor(self, folder_name: str, module_key: str):
        """Load an executor module from a sibling folder."""
        module_path = Path(__file__).parent.parent / folder_name / "executor.py"
        if not module_path.exists():
            raise FileNotFoundError(f"Executor module not found: {module_path}")
        spec = importlib.util.spec_from_file_location(module_key, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.create_executor(self.config)

    async def run(self, action: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if action == "analyze":
            return await self.analyze(**inputs)
        raise ValueError(f"Unknown action: {action}")

    async def analyze(
        self,
        path: str,
        languages: list = None,
        structure: dict = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Run full quality analysis."""
        structure = structure or await self._static.analyze_structure(path)
        dependencies = await self._static.analyze_dependencies(path, languages)
        code_quality = await self._static.analyze_quality(path, languages)
        security = await self._security.scan(path, languages)

        git_history = {}
        if (Path(path) / ".git").exists():
            git_history = await self._git.analyze_history(path=path)

        scores = await self._scoring.calculate(
            structure=structure,
            git_history=git_history,
            dependencies=dependencies,
            security=security,
            code_quality=code_quality,
        )

        documentation_quality = {
            "score": self._doc_score(structure),
            "has_readme": structure.get("has_readme", False),
            "readme_has_usage": structure.get("readme_has_usage", False),
            "readme_has_install": structure.get("readme_has_install", False),
            "has_docs_folder": structure.get("has_docs_folder", False),
            "has_architecture_docs": structure.get("has_architecture_docs", False),
        }

        return {
            "repo_health": scores.get("repo_health", 0),
            "tech_debt": scores.get("tech_debt", 0),
            "security_score": scores.get("security_score", 0),
            "product_level": scores.get("product_level", "Unknown"),
            "overall_readiness": scores.get("overall_readiness", 0),
            "code_quality": code_quality,
            "documentation_quality": documentation_quality,
            "structure": structure,
            "dependencies": dependencies,
            "git_history": git_history,
            "security": security,
            "breakdown": scores.get("breakdown", {}),
        }

    def _doc_score(self, structure: dict) -> int:
        """Compute documentation score on 0-3 scale."""
        if not structure.get("has_readme", False):
            return 0
        if structure.get("has_docs_folder") and structure.get("has_architecture_docs"):
            return 3
        if structure.get("readme_has_usage") and structure.get("readme_has_install"):
            return 2
        return 1


def create_executor(config: Dict[str, Any] = None) -> QualityAnalyzerExecutor:
    return QualityAnalyzerExecutor(config)
