"""
MCP Server for Audit Platform - Complete Edition

Features:
- Full repository audit
- 8 Estimation Methodologies
- PERT 3-Point Analysis
- AI Efficiency Comparison
- ROI Calculator
- 8 Regional Rate Profiles
- Document Management
"""
import asyncio
import json
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import formulas
try:
    from executors import cost_estimator
    from executors.cost_estimator.formulas import (
        REGIONAL_RATES,
        METHODOLOGIES,
        estimate_cocomo_modern,
        estimate_all_methodologies,
        estimate_methodology,
        calculate_pert,
        estimate_ai_efficiency,
        calculate_roi,
        get_all_regional_costs,
        get_all_formulas,
        get_all_constants,
    )
    FORMULAS_AVAILABLE = True
except ImportError:
    FORMULAS_AVAILABLE = False


class AuditMCPServer:
    """MCP Server exposing audit tools to Claude"""

    def get_tools(self) -> list[dict]:
        """Tools available to Claude via MCP"""
        tools = [
            # ─────────────────────────────────────────────────────────────
            # MAIN AUDIT TOOL
            # ─────────────────────────────────────────────────────────────
            {
                "name": "audit",
                "description": """Run repository audit. Choose task based on need:
- quick_scan: Fast overview (5 sec) - files, LOC, languages
- detect_type: Project type detection - framework, architecture
- check_quality: Quality analysis - repo health, tech debt, security
- check_compliance: Contract/policy compliance check
- estimate_cost: Development cost and IP value estimation
- full_audit: Complete audit with all checks (3-5 min)""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Git URL (https://github.com/...) or local path (/path/to/dir)"
                        },
                        "task": {
                            "type": "string",
                            "enum": ["quick_scan", "detect_type", "check_quality",
                                    "check_compliance", "estimate_cost", "full_audit"],
                            "default": "quick_scan"
                        },
                        "branch": {"type": "string", "default": "main"},
                        "policy_id": {
                            "type": "string",
                            "description": "Policy to check against: global_fund_r13, standard, enterprise"
                        },
                        "region": {
                            "type": "string",
                            "enum": list(REGIONAL_RATES.keys()) if FORMULAS_AVAILABLE else ["ua", "eu", "us"],
                            "default": "ua",
                            "description": "Region for cost calculation"
                        }
                    },
                    "required": ["source"]
                }
            },
            {
                "name": "audit_preflight",
                "description": "Preflight planner: quick type detection and a recommended audit strategy before running.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Git URL (https://github.com/...) or local path (/path/to/dir)"
                        },
                        "goal": {
                            "type": "string",
                            "enum": ["overview", "type", "quality", "compliance", "cost", "full"],
                            "description": "Primary goal for audit strategy selection"
                        },
                        "branch": {"type": "string", "default": "main"},
                        "policy_id": {
                            "type": "string",
                            "description": "Policy to check against: global_fund_r13, standard, enterprise"
                        },
                        "region": {
                            "type": "string",
                            "enum": list(REGIONAL_RATES.keys()) if FORMULAS_AVAILABLE else ["ua", "eu", "us"],
                            "default": "ua"
                        }
                    },
                    "required": ["source"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # COCOMO II ESTIMATION
            # ─────────────────────────────────────────────────────────────
            {
                "name": "estimate_cocomo",
                "description": "COCOMO II Modern estimate. Formula: Effort = 0.5 × (KLOC)^0.85 × EAF. Returns hours, cost for all 8 regions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "loc": {"type": "integer", "description": "Lines of code"},
                        "tech_debt_score": {"type": "integer", "description": "Tech debt 0-15", "default": 10},
                        "team_experience": {"type": "string", "enum": ["low", "nominal", "high"], "default": "nominal"},
                    },
                    "required": ["loc"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # 8 METHODOLOGIES
            # ─────────────────────────────────────────────────────────────
            {
                "name": "estimate_comprehensive",
                "description": "All 8 methodologies: COCOMO II, Gartner, IEEE 1063, Microsoft, Google, PMI, SEI SLIM, Function Points. Includes PERT analysis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "loc": {"type": "integer"},
                        "complexity": {"type": "number", "default": 1.0, "description": "0.5-3.0"},
                        "hourly_rate": {"type": "number", "default": 35},
                        "estimation_mode": {
                            "type": "string",
                            "enum": ["software", "documentation", "all"],
                            "default": "software",
                            "description": "Limit methodologies by domain"
                        },
                        "doc_words": {"type": "integer", "description": "Documentation word count (for documentation mode)"},
                        "doc_pages": {"type": "integer", "description": "Documentation page count (for documentation mode)"},
                    },
                    "required": ["loc"]
                }
            },
            {
                "name": "estimate_methodology",
                "description": "Single methodology estimate with formula details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "methodology": {
                            "type": "string",
                            "enum": list(METHODOLOGIES.keys()) if FORMULAS_AVAILABLE else ["cocomo", "gartner", "ieee"]
                        },
                        "loc": {"type": "integer"},
                        "complexity": {"type": "number", "default": 1.0},
                        "hourly_rate": {"type": "number", "default": 35},
                        "doc_words": {"type": "integer"},
                        "doc_pages": {"type": "integer"},
                    },
                    "required": ["methodology", "loc"]
                }
            },
            {
                "name": "list_methodologies",
                "description": "List all 8 estimation methodologies with formulas",
                "inputSchema": {"type": "object", "properties": {}}
            },

            # ─────────────────────────────────────────────────────────────
            # PERT
            # ─────────────────────────────────────────────────────────────
            {
                "name": "estimate_pert",
                "description": "PERT 3-point: Expected = (O + 4×M + P) / 6, σ = (P - O) / 6. Returns 68%, 95%, 99% CI.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "optimistic_hours": {"type": "number"},
                        "most_likely_hours": {"type": "number"},
                        "pessimistic_hours": {"type": "number"},
                        "hourly_rate": {"type": "number", "default": 35},
                    },
                    "required": ["optimistic_hours", "most_likely_hours", "pessimistic_hours"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # AI EFFICIENCY
            # ─────────────────────────────────────────────────────────────
            {
                "name": "estimate_ai_efficiency",
                "description": "Compare: Pure Human (25 hrs/KLOC) vs AI-Assisted (8 hrs/KLOC) vs Hybrid (6.5 hrs/KLOC)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "loc": {"type": "integer"},
                        "hourly_rate": {"type": "number", "default": 35},
                        "complexity": {"type": "number", "default": 1.0},
                    },
                    "required": ["loc"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # ROI
            # ─────────────────────────────────────────────────────────────
            {
                "name": "calculate_roi",
                "description": "ROI analysis: payback period, NPV 3yr, ROI 1yr/3yr %",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "investment_cost": {"type": "number"},
                        "annual_support_savings": {"type": "number", "default": 0},
                        "annual_training_savings": {"type": "number", "default": 0},
                        "annual_efficiency_gain": {"type": "number", "default": 0},
                        "annual_risk_reduction": {"type": "number", "default": 0},
                        "maintenance_percent": {"type": "number", "default": 20},
                    },
                    "required": ["investment_cost"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # REGIONAL COSTS
            # ─────────────────────────────────────────────────────────────
            {
                "name": "get_regional_costs",
                "description": "Get cost for all 8 regions (UA, PL, EU, DE, UK, US, IN, UA_Compliance)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "hours": {"type": "number", "description": "Hours to estimate cost for"},
                    },
                    "required": ["hours"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # FORMULAS & CONSTANTS
            # ─────────────────────────────────────────────────────────────
            {
                "name": "get_formulas",
                "description": "Get all formulas: COCOMO II, PERT, 8 methodologies, AI efficiency, ROI",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "get_constants",
                "description": "Get all constants: COCOMO, thresholds, multipliers, rates",
                "inputSchema": {"type": "object", "properties": {}}
            },

            # ─────────────────────────────────────────────────────────────
            # DOCUMENT MANAGEMENT
            # ─────────────────────────────────────────────────────────────
            {
                "name": "upload_document_file",
                "description": "Upload contract or policy document file (PDF, DOCX) for compliance checking",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to document file"},
                        "doc_type": {"type": "string", "enum": ["contract", "policy"], "default": "contract"},
                        "name": {"type": "string", "description": "Custom name for the document"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "list_policies",
                "description": "List available saved policies for compliance checking",
                "inputSchema": {"type": "object", "properties": {}}
            },

            # ─────────────────────────────────────────────────────────────
            # EXPLANATION & INTERPRETATION
            # ─────────────────────────────────────────────────────────────
            {
                "name": "explain_metric",
                "description": "Explain a metric in business-friendly terms",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "enum": ["repo_health", "tech_debt", "security_score",
                                    "complexity", "test_coverage", "product_level"]
                        },
                        "value": {"type": "number"},
                        "context": {"type": "string", "description": "Additional context"}
                    },
                    "required": ["metric", "value"]
                }
            },
            {
                "name": "explain_product_level",
                "description": "Explain what a product level means and how to reach the next level",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["R&D Spike", "Prototype", "MVP", "Alpha", "Beta", "RC", "Production"]
                        }
                    },
                    "required": ["level"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # RECOMMENDATIONS
            # ─────────────────────────────────────────────────────────────
            {
                "name": "get_recommendations",
                "description": "Get prioritized recommendations based on audit results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_health": {"type": "number"},
                        "tech_debt": {"type": "number"},
                        "security_score": {"type": "number"},
                        "current_level": {"type": "string"},
                        "target_level": {"type": "string"}
                    },
                    "required": ["repo_health", "tech_debt"]
                }
            },

            # ─────────────────────────────────────────────────────────────
            # LOAD EXISTING RESULTS
            # ─────────────────────────────────────────────────────────────
            {
                "name": "load_results",
                "description": "Load audit results from JSON file for analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to results.json"}
                    },
                    "required": ["file_path"]
                }
            }
        ]

        return tools

    async def handle_tool(self, name: str, args: dict) -> dict:
        """Handle tool calls"""

        # Audit tools
        if name == "audit":
            return await self._run_audit(args)
        elif name == "audit_preflight":
            return await self._preflight(args)

        # Estimation tools
        elif name == "estimate_cocomo":
            return self._estimate_cocomo(args)
        elif name == "estimate_comprehensive":
            return self._estimate_comprehensive(args)
        elif name == "estimate_methodology":
            return self._estimate_methodology(args)
        elif name == "list_methodologies":
            return self._list_methodologies()
        elif name == "estimate_pert":
            return self._estimate_pert(args)
        elif name == "estimate_ai_efficiency":
            return self._estimate_ai_efficiency(args)
        elif name == "calculate_roi":
            return self._calculate_roi(args)
        elif name == "get_regional_costs":
            return self._get_regional_costs(args)
        elif name == "get_formulas":
            return self._get_formulas()
        elif name == "get_constants":
            return self._get_constants()

        # Document tools
        elif name == "upload_document_file":
            return await self._upload_document(args)
        elif name == "list_policies":
            return self._list_policies()

        # Explanation tools
        elif name == "explain_metric":
            return self._explain_metric(args)
        elif name == "explain_product_level":
            return self._explain_level(args)
        elif name == "get_recommendations":
            return self._get_recommendations(args)
        elif name == "load_results":
            return self._load_results(args)

        return {"error": f"Unknown tool: {name}"}

    # =========================================================================
    # ESTIMATION TOOLS
    # =========================================================================

    def _estimate_cocomo(self, args: dict) -> dict:
        """COCOMO II Modern estimate."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        loc = args.get("loc", 10000)
        tech_debt = args.get("tech_debt_score", 10)
        experience = args.get("team_experience", "nominal")

        result = estimate_cocomo_modern(loc, tech_debt, experience)
        hours = result["hours"]["typical"]
        regional = get_all_regional_costs(hours)

        payload = {
            **result,
            "cost_by_region": regional["regions"],
        }
        return self._attach_validation(payload, kloc=loc / 1000, hourly_rate=args.get("hourly_rate"))

    def _estimate_comprehensive(self, args: dict) -> dict:
        """All 8 methodologies."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        payload = estimate_all_methodologies(
            loc=args.get("loc", 10000),
            complexity=args.get("complexity", 1.0),
            hourly_rate=args.get("hourly_rate", 35),
            estimation_mode=args.get("estimation_mode", "software"),
            doc_words=args.get("doc_words"),
            doc_pages=args.get("doc_pages"),
        )
        return self._attach_validation(payload, kloc=args.get("loc", 10000) / 1000, hourly_rate=args.get("hourly_rate", 35))

    def _estimate_methodology(self, args: dict) -> dict:
        """Single methodology."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        payload = estimate_methodology(
            methodology=args["methodology"],
            loc=args["loc"],
            complexity=args.get("complexity", 1.0),
            hourly_rate=args.get("hourly_rate", 35),
            doc_words=args.get("doc_words"),
            doc_pages=args.get("doc_pages"),
        )
        return self._attach_validation(payload, kloc=args["loc"] / 1000, hourly_rate=args.get("hourly_rate", 35))

    def _list_methodologies(self) -> dict:
        """List all methodologies."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        return {
            "count": len(METHODOLOGIES),
            "methodologies": METHODOLOGIES,
        }

    def _estimate_pert(self, args: dict) -> dict:
        """PERT 3-point analysis."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        pert = calculate_pert(
            args["optimistic_hours"],
            args["most_likely_hours"],
            args["pessimistic_hours"],
        )

        rate = args.get("hourly_rate", 35)
        pert["cost"] = {
            "expected": round(pert["expected"] * rate, 2),
            "range_68": {
                "min": round(pert["confidence_68"]["min"] * rate, 2),
                "max": round(pert["confidence_68"]["max"] * rate, 2),
            },
            "range_95": {
                "min": round(pert["confidence_95"]["min"] * rate, 2),
                "max": round(pert["confidence_95"]["max"] * rate, 2),
            },
        }

        return self._attach_validation(pert, kloc=args.get("loc", 0) / 1000 if args.get("loc") else 0, hourly_rate=rate)

    def _estimate_ai_efficiency(self, args: dict) -> dict:
        """AI efficiency comparison."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        payload = estimate_ai_efficiency(
            loc=args["loc"],
            hourly_rate=args.get("hourly_rate", 35),
            complexity=args.get("complexity", 1.0),
        )
        return self._attach_validation(payload, kloc=args["loc"] / 1000, hourly_rate=args.get("hourly_rate", 35))

    def _calculate_roi(self, args: dict) -> dict:
        """ROI analysis."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        payload = calculate_roi(
            investment_cost=args["investment_cost"],
            annual_support_savings=args.get("annual_support_savings", 0),
            annual_training_savings=args.get("annual_training_savings", 0),
            annual_efficiency_gain=args.get("annual_efficiency_gain", 0),
            annual_risk_reduction=args.get("annual_risk_reduction", 0),
            maintenance_percent=args.get("maintenance_percent", 20),
        )
        return self._attach_validation(payload, kloc=args.get("loc", 0) / 1000 if args.get("loc") else 0, hourly_rate=args.get("hourly_rate"))

    def _attach_validation(self, payload: dict, kloc: float, hourly_rate: float = None) -> dict:
        """Attach validation bounds if available from HTTP server module."""
        strict = os.environ.get("STRICT_ESTIMATION", "true").lower() in {"1", "true", "yes"}
        rate_min = float(os.environ.get("RATE_MIN", "5"))
        rate_max = float(os.environ.get("RATE_MAX", "300"))
        hours_per_kloc_min = float(os.environ.get("HOURS_PER_KLOC_MIN", "2"))
        hours_per_kloc_max = float(os.environ.get("HOURS_PER_KLOC_MAX", "200"))

        total_hours = payload.get("hours")
        if isinstance(payload.get("hours"), dict):
            total_hours = payload["hours"].get("typical") or payload["hours"].get("expected")
        total_cost = None
        if payload.get("cost"):
            total_cost = payload["cost"].get("expected") or payload["cost"].get("typical")
        if total_hours and total_cost is not None:
            hourly_rate_val = hourly_rate or (total_cost / total_hours if total_hours else 0)
            hours_per_kloc = (total_hours / kloc) if kloc else 0
            errors = []
            warnings = []
            if kloc:
                if hours_per_kloc < hours_per_kloc_min:
                    errors.append(f"Hours/KLOC ({hours_per_kloc:.1f}) below minimum ({hours_per_kloc_min})")
                elif hours_per_kloc > hours_per_kloc_max:
                    errors.append(f"Hours/KLOC ({hours_per_kloc:.1f}) above maximum ({hours_per_kloc_max})")
            if hourly_rate_val:
                if hourly_rate_val < rate_min:
                    warnings.append(f"Rate ${hourly_rate_val}/hr below minimum ${rate_min}")
                elif hourly_rate_val > rate_max:
                    warnings.append(f"Rate ${hourly_rate_val}/hr above maximum ${rate_max}")
            validation = {
                "valid": len(errors) == 0,
                "total_hours": total_hours,
                "total_cost": total_cost,
                "kloc": kloc,
                "hourly_rate": hourly_rate_val,
                "hours_per_kloc": hours_per_kloc,
                "warnings": warnings,
                "errors": errors,
                "bounds": {
                    "rate_range": f"${rate_min}-${rate_max}/hr",
                    "hours_per_kloc_range": f"{hours_per_kloc_min}-{hours_per_kloc_max}",
                },
            }
            payload["validation"] = validation
            if strict and not validation["valid"]:
                return {"error": "Estimate failed validation", "validation": validation}
        return payload

    def _get_regional_costs(self, args: dict) -> dict:
        """Regional costs for all 8 regions."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        return get_all_regional_costs(args["hours"])

    def _get_formulas(self) -> dict:
        """Get all formulas."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        return get_all_formulas()

    def _get_constants(self) -> dict:
        """Get all constants."""
        if not FORMULAS_AVAILABLE:
            return {"error": "Formulas module not available"}

        return get_all_constants()

    # =========================================================================
    # AUDIT TOOLS
    # =========================================================================

    async def _run_audit(self, args: dict) -> dict:
        """Run audit via CLI runner"""
        try:
            from run import run_audit
            return await run_audit(
                source=args["source"],
                task=args.get("task", "quick_scan"),
                branch=args.get("branch", "main"),
                policy_id=args.get("policy_id"),
                region=args.get("region", "ua"),
                verbose=False
            )
        except ImportError:
            return {"error": "Audit runner not available"}

    async def _preflight(self, args: dict) -> dict:
        """Preflight planner for selecting audit strategy."""
        try:
            from run import run_audit
        except ImportError:
            return {"error": "Audit runner not available"}

        source = args["source"]
        branch = args.get("branch", "main")
        goal = (args.get("goal") or "").lower()
        policy_id = args.get("policy_id")
        region = args.get("region", "ua")

        # Run preflight workflow (quick_scan + detect_type)
        analysis = await run_audit(
            source=source,
            task="preflight",
            branch=branch,
            policy_id=policy_id,
            region=region,
            verbose=False
        )

        outputs = analysis.get("results", {}).get("outputs", {})
        stages = analysis.get("results", {}).get("stages", {})
        quick_scan = stages.get("quick_scan", {}).get("outputs", {})
        detect_type = stages.get("detect_type", {}).get("outputs", {})

        recommended_task, rationale, questions = self._recommend_task(goal, policy_id, quick_scan, detect_type)

        return {
            "source": source,
            "goal": goal or None,
            "project_snapshot": {
                "files": outputs.get("files"),
                "loc": outputs.get("loc"),
                "languages": outputs.get("languages"),
                "project_type": outputs.get("project_type"),
            },
            "recommended_task": recommended_task,
            "rationale": rationale,
            "questions": questions,
            "next_call": {
                "tool": "audit",
                "arguments": {
                    "source": source,
                    "task": recommended_task,
                    "branch": branch,
                    "policy_id": policy_id,
                    "region": region,
                },
            },
            "standard_cost_method": "cocomo_modern_v1",
        }

    def _recommend_task(self, goal: str, policy_id: str, scan: dict, type_info: dict):
        """Deterministic task selection based on inputs."""
        if goal == "overview":
            return "quick_scan", "Запрошено швидкий огляд.", []
        if goal == "type":
            return "detect_type", "Запрошено визначення типу проєкту.", []
        if goal == "quality":
            return "check_quality", "Запрошено оцінку якості.", []
        if goal == "compliance":
            return "check_compliance", "Запрошено перевірку відповідності.", []
        if goal == "cost":
            return "estimate_cost", "Запрошено оцінку вартості.", []
        if goal == "full":
            return "full_audit", "Запрошено повний аудит.", []

        if policy_id:
            return "check_compliance", "Є policy_id, тому рекомендовано compliance.", []

        loc = scan.get("loc", 0) if isinstance(scan, dict) else 0
        if loc == 0:
            return "quick_scan", "Немає LOC; спершу потрібен quick_scan.", [
                "Яка основна мета аудиту: якість, відповідність, вартість чи повний?"
            ]

        return "check_quality", "Типова стратегія для старту: перевірка якості.", [
            "Потрібна перевірка відповідності до політики/контракту?",
            "Потрібна оцінка вартості/часу розробки?",
        ]

    async def _upload_document(self, args: dict) -> dict:
        """Upload and parse document"""
        try:
            from executors.document_loader.executor import create_executor
            loader = create_executor()
            return await loader.parse_file(
                args["file_path"],
                args.get("doc_type", "contract")
            )
        except ImportError:
            return {"error": "Document loader not available"}

    def _list_policies(self) -> dict:
        """List saved policies"""
        return {
            "policies": [
                {"id": "global_fund_r13", "name": "Global Fund R13", "requirements": 6},
                {"id": "standard", "name": "Standard Requirements", "requirements": 3},
                {"id": "enterprise", "name": "Enterprise Requirements", "requirements": 7},
            ]
        }

    def _explain_metric(self, args: dict) -> dict:
        """Explain metric in business terms"""
        metric = args["metric"]
        value = args["value"]

        explanations = {
            "repo_health": {
                "name": "Repository Health",
                "max": 12,
                "meaning": "Measures project organization: documentation, tests, CI/CD, containerization",
                "business_impact": "Higher = easier maintenance, faster onboarding, lower risk"
            },
            "tech_debt": {
                "name": "Technical Debt Score",
                "max": 15,
                "meaning": "Code quality: complexity, duplication, outdated dependencies",
                "business_impact": "Higher = cleaner code, faster development, fewer bugs"
            },
            "security_score": {
                "name": "Security Score",
                "max": 3,
                "meaning": "Security posture: vulnerabilities, secrets exposure, security policies",
                "business_impact": "Critical for production use and handling sensitive data"
            }
        }

        info = explanations.get(metric, {"name": metric, "max": 100, "meaning": "", "business_impact": ""})
        percent = (value / info["max"]) * 100 if info["max"] else 0

        if percent >= 80:
            status = "excellent"
        elif percent >= 60:
            status = "good"
        elif percent >= 40:
            status = "needs improvement"
        else:
            status = "critical"

        return {
            "metric": info["name"],
            "value": value,
            "max": info["max"],
            "percent": round(percent, 1),
            "status": status,
            "meaning": info["meaning"],
            "business_impact": info["business_impact"]
        }

    def _explain_level(self, args: dict) -> dict:
        """Explain product level"""
        levels = {
            "R&D Spike": {
                "emoji": "🧪",
                "description": "Experimental code, proof of concept",
                "suitable_for": ["Internal experiments", "Feasibility testing"],
                "not_for": ["Production", "Customer-facing"],
                "next_level": "Prototype",
                "to_upgrade": ["Add README", "Basic error handling", "Document main functions"]
            },
            "Prototype": {
                "emoji": "🔧",
                "description": "Working prototype, demonstrates functionality",
                "suitable_for": ["Demos", "User feedback", "Limited internal testing"],
                "not_for": ["Production", "Real user data"],
                "next_level": "MVP",
                "to_upgrade": ["Add unit tests (40%+)", "Input validation", "CI pipeline"]
            },
            "MVP": {
                "emoji": "🎯",
                "description": "Minimum Viable Product",
                "suitable_for": ["Early adopters", "Basic production use"],
                "not_for": ["High-scale production"],
                "next_level": "Alpha",
                "to_upgrade": ["50%+ test coverage", "Error handling", "Basic monitoring"]
            },
            "Alpha": {
                "emoji": "🛠️",
                "description": "Ready for internal team use",
                "suitable_for": ["Team workflows", "Non-critical processes"],
                "not_for": ["External customers", "Mission-critical"],
                "next_level": "Beta",
                "to_upgrade": ["60%+ test coverage", "API docs", "Docker support", "CD pipeline"]
            },
            "Beta": {
                "emoji": "📦",
                "description": "Can be integrated into platform",
                "suitable_for": ["Platform integration", "Internal services"],
                "not_for": ["Direct customer access without gateway"],
                "next_level": "RC",
                "to_upgrade": ["Security audit", "Performance optimization", "80%+ tests", "Full docs"]
            },
            "RC": {
                "emoji": "🎖️",
                "description": "Release Candidate",
                "suitable_for": ["Final testing", "Pre-production"],
                "not_for": ["High-risk deployment without review"],
                "next_level": "Production",
                "to_upgrade": ["Final security review", "Load testing", "Rollback plan"]
            },
            "Production": {
                "emoji": "🚀",
                "description": "Production-ready quality",
                "suitable_for": ["Production", "Customer-facing", "Critical processes"],
                "not_for": [],
                "next_level": None,
                "to_upgrade": ["Regular security updates", "Dependency updates", "Monitoring"]
            }
        }
        return levels.get(args["level"], {"error": "Unknown level"})

    def _get_recommendations(self, args: dict) -> dict:
        """Generate recommendations"""
        health = args.get("repo_health", 0)
        debt = args.get("tech_debt", 0)
        security = args.get("security_score", 3)

        recommendations = []

        if security < 2:
            recommendations.append({
                "priority": "critical",
                "category": "security",
                "action": "Fix security vulnerabilities immediately",
                "impact": "Blocks production deployment"
            })

        if health < 6:
            recommendations.append({
                "priority": "high",
                "category": "documentation",
                "action": "Add README with setup instructions",
                "impact": "Improves onboarding"
            })

        if not args.get("has_tests", health >= 6):
            recommendations.append({
                "priority": "high",
                "category": "testing",
                "action": "Add unit tests (target 40%+ coverage)",
                "impact": "Reduces bugs, enables CI"
            })

        if debt < 10:
            recommendations.append({
                "priority": "medium",
                "category": "code_quality",
                "action": "Reduce code complexity",
                "impact": "Easier maintenance"
            })

        return {
            "recommendations": recommendations[:5],
            "total_issues": len(recommendations)
        }

    def _load_results(self, args: dict) -> dict:
        """Load results from JSON file"""
        try:
            path = Path(args["file_path"])
            if not path.exists():
                return {"error": f"File not found: {args['file_path']}"}
            return json.loads(path.read_text())
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# MCP PROTOCOL
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    """Run MCP server (stdio)"""
    server = AuditMCPServer()

    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            request = json.loads(line)
            method = request.get("method")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "audit-platform",
                            "version": "2.0.0",
                            "description": "Complete audit with 8 methodologies, PERT, AI efficiency, ROI",
                        },
                    }
                }

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"tools": server.get_tools()}
                }

            elif method == "tools/call":
                params = request.get("params", {})
                result = await server.handle_tool(
                    params.get("name"),
                    params.get("arguments", {})
                )
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result, indent=2, default=str)
                        }]
                    }
                }

            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {}
                }

            print(json.dumps(response), flush=True)

        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
