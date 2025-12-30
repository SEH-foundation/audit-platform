"""
Type Detector Executor
Detects project type, framework, architecture, and maturity.
"""
from typing import Any, Dict, List, Set
from pathlib import Path
import json
import logging
import importlib.util

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseExecutor

logger = logging.getLogger(__name__)


class TypeDetectorExecutor(BaseExecutor):
    """Executor for project type detection."""

    name = "type-detector"

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
        if action == "detect":
            return await self.detect(**inputs)
        raise ValueError(f"Unknown action: {action}")

    async def detect(self, path: str, scan: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Detect project type and framework."""
        repo_path = Path(path)
        structure = await self._static.analyze_structure(path)
        languages = structure.get("languages", []) or (scan or {}).get("languages", [])

        deps = self._collect_dependencies(repo_path)
        framework = self._detect_framework(deps, repo_path)
        project_type = self._detect_project_type(deps, repo_path, structure, framework)
        architecture = self._detect_architecture(repo_path)
        maturity_level = self._detect_maturity(structure)

        return {
            "project_type": project_type,
            "framework": framework or "unknown",
            "architecture": architecture,
            "maturity_level": maturity_level,
            "languages": languages,
        }

    def _collect_dependencies(self, repo_path: Path) -> Set[str]:
        deps: Set[str] = set()
        deps.update(self._read_requirements(repo_path / "requirements.txt"))
        deps.update(self._read_pyproject(repo_path / "pyproject.toml"))
        deps.update(self._read_package_json(repo_path / "package.json"))
        deps.update(self._read_go_mod(repo_path / "go.mod"))
        deps.update(self._read_cargo(repo_path / "Cargo.toml"))
        return deps

    def _read_requirements(self, path: Path) -> Set[str]:
        if not path.exists():
            return set()
        deps = set()
        for line in path.read_text(errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                name = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0]
                deps.add(name.lower())
        return deps

    def _read_pyproject(self, path: Path) -> Set[str]:
        if not path.exists():
            return set()
        deps = set()
        try:
            content = path.read_text(errors="ignore").lower()
            markers = ["django", "flask", "fastapi", "starlette", "typer", "click", "airflow", "dagster"]
            for marker in markers:
                if marker in content:
                    deps.add(marker)
        except Exception:
            pass
        return deps

    def _read_package_json(self, path: Path) -> Set[str]:
        if not path.exists():
            return set()
        deps = set()
        try:
            data = json.loads(path.read_text(errors="ignore"))
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                deps.update(name.lower() for name in data.get(section, {}).keys())
        except Exception:
            pass
        return deps

    def _read_go_mod(self, path: Path) -> Set[str]:
        if not path.exists():
            return set()
        deps = set()
        try:
            for line in path.read_text(errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                if line.startswith("require") or line.startswith("module"):
                    continue
                if line.startswith(")"):
                    continue
                parts = line.split()
                if parts:
                    deps.add(parts[0].lower())
        except Exception:
            pass
        return deps

    def _read_cargo(self, path: Path) -> Set[str]:
        if not path.exists():
            return set()
        deps = set()
        try:
            content = path.read_text(errors="ignore").lower()
            for marker in ["actix-web", "rocket", "axum", "tokio"]:
                if marker in content:
                    deps.add(marker)
        except Exception:
            pass
        return deps

    def _detect_framework(self, deps: Set[str], repo_path: Path) -> str:
        framework_map = {
            "nextjs": {"next"},
            "react": {"react"},
            "vue": {"vue", "nuxt"},
            "angular": {"@angular/core"},
            "svelte": {"svelte", "sveltekit"},
            "express": {"express"},
            "nestjs": {"@nestjs/core"},
            "fastify": {"fastify"},
            "django": {"django"},
            "flask": {"flask"},
            "fastapi": {"fastapi"},
            "spring": {"spring-boot"},
            "gin": {"github.com/gin-gonic/gin"},
            "echo": {"github.com/labstack/echo"},
            "fiber": {"github.com/gofiber/fiber"},
            "actix": {"actix-web"},
            "rocket": {"rocket"},
        }
        for name, markers in framework_map.items():
            if deps.intersection(markers):
                return name
        return ""

    def _detect_project_type(
        self,
        deps: Set[str],
        repo_path: Path,
        structure: Dict[str, Any],
        framework: str,
    ) -> str:
        if self._is_mobile(repo_path):
            return "mobile_app"
        if self._is_infra(repo_path):
            return "infrastructure"
        if framework in {"express", "nestjs", "fastify", "django", "flask", "fastapi", "spring", "gin", "echo", "fiber", "actix", "rocket"}:
            return "web_service"
        if framework in {"nextjs", "react", "vue", "angular", "svelte"}:
            return "web_app"
        if self._is_cli(repo_path, deps):
            return "cli"
        if self._is_data_pipeline(deps):
            return "data_pipeline"
        if self._is_ml_model(deps):
            return "ml_model"
        if self._is_library(repo_path, structure):
            return "library"
        return "unknown"

    def _detect_architecture(self, repo_path: Path) -> str:
        if (repo_path / "packages").exists() or (repo_path / "apps").exists():
            return "monorepo"
        compose = repo_path / "docker-compose.yml"
        if compose.exists():
            try:
                content = compose.read_text(errors="ignore")
                if "services:" in content and content.count("\n  ") >= 6:
                    return "microservices"
            except Exception:
                pass
        return "monolith"

    def _detect_maturity(self, structure: Dict[str, Any]) -> str:
        signals = sum(
            1 for key in [
                "has_readme",
                "has_tests",
                "has_ci",
                "has_changelog",
                "has_version_file",
                "has_docs_folder",
            ]
            if structure.get(key, False)
        )
        if signals >= 5:
            return "production"
        if signals >= 4:
            return "beta"
        if signals >= 2:
            return "prototype"
        return "spike"

    def _is_mobile(self, repo_path: Path) -> bool:
        return any(repo_path.rglob("AndroidManifest.xml")) or any(repo_path.rglob("*.xcodeproj"))

    def _is_infra(self, repo_path: Path) -> bool:
        infra_markers = ["terraform", "helm", "kustomize", "ansible", "cloudformation"]
        for marker in infra_markers:
            if list(repo_path.rglob(f"*{marker}*")):
                return True
        return False

    def _is_cli(self, repo_path: Path, deps: Set[str]) -> bool:
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(errors="ignore"))
                if data.get("bin"):
                    return True
            except Exception:
                pass
        return bool(deps.intersection({"click", "typer", "argparse"}))

    def _is_data_pipeline(self, deps: Set[str]) -> bool:
        return bool(deps.intersection({"airflow", "prefect", "dagster", "luigi", "dbt"}))

    def _is_ml_model(self, deps: Set[str]) -> bool:
        return bool(deps.intersection({"tensorflow", "torch", "pytorch", "scikit-learn", "xgboost", "lightgbm"}))

    def _is_library(self, repo_path: Path, structure: Dict[str, Any]) -> bool:
        has_package = (repo_path / "setup.py").exists() or (repo_path / "pyproject.toml").exists()
        return has_package and not structure.get("has_tests", False) and not structure.get("has_ci", False)


def create_executor(config: Dict[str, Any] = None) -> TypeDetectorExecutor:
    return TypeDetectorExecutor(config)
