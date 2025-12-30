# Estimation Formulas

This document describes the **fixed standard** estimation method and all
auxiliary formulas used by audit-platform. The goal is deterministic and
repeatable outputs with no hidden heuristics.

## Where These Formulas Are Used
- Standard cost estimate (primary):
  - `executors/cost_estimator/formulas.py` -> `estimate_cocomo_modern`
  - `executors/cost_estimator/executor.py` -> `estimate_standard`, `full_estimate`
  - `gateway/mcp/http_server.py` -> `estimate_cost`
- Additional methods (optional):
  - `estimate_methodology`, `estimate_comprehensive`
  - `estimate_pert`, `estimate_ai_efficiency`, `calculate_roi`

## Standard Method: COCOMO II Modern (Fixed)
Method ID: `cocomo_modern_v1`

### Inputs
- `LOC` (lines of code)
- `team_experience`: `low | nominal | high`
- `tech_debt_score`: 0–15

### Constants
From `COCOMO_CONSTANTS`:
- `a = 0.5`
- `b = 0.85`
- `c = 2.0`
- `d = 0.35`
- `hours_per_pm = 160`

### Step 1: Convert LOC to KLOC
```
KLOC = max(LOC / 1000, 0.1)
```

### Step 2: Effort Adjustment Factor (EAF)
EAF is a product of:
- team experience multiplier
- tech debt multiplier

Team experience multipliers:
- low = 1.30
- nominal = 1.00
- high = 0.80

Tech debt multipliers:
- 0–3   -> 1.50
- 4–6   -> 1.30
- 7–9   -> 1.15
- 10–12 -> 1.05
- 13–15 -> 1.00

```
EAF = team_experience_multiplier × tech_debt_multiplier
```

### Step 3: Effort (Person-Months)
```
Effort_PM = a × (KLOC ^ b) × EAF
```

### Step 4: Hours
```
Hours = Effort_PM × hours_per_pm
```

### Step 5: Schedule (Months)
```
Schedule_months = c × (Effort_PM ^ d)
```

### Step 6: Team Size
```
Team_size = Effort_PM / max(Schedule_months, 0.5)
```

### Step 7: Uncertainty Range
Used only for min/max reporting, not for changing the base effort:
```
Hours_min = Hours × 0.8
Hours_max = Hours × 1.2
```

### Step 8: Regional Cost
Typical cost uses regional `middle` rate:
```
Cost_typical = Hours_typical × region_rate.middle
```
Rates come from `REGIONAL_RATES` and are fixed per region.

### Derived Outputs
The standard workflow (`full_estimate`) also reports:
- `timeline_weeks` = `schedule_months × 4.3`
- `maintenance_cost_monthly` = `dev_cost_usd × 0.20 / 12`
- `ip_value_usd` = `dev_cost_usd × 1.20`

## Auxiliary Methods

### PERT (3-point estimate)
```
Expected = (O + 4×M + P) / 6
StdDev   = (P - O) / 6
```
Returns confidence ranges at 68/95/99%.

### AI Efficiency
Compares hours by productivity in hours per KLOC:
- pure_human: 25
- ai_assisted: 8
- hybrid: 6.5

### ROI
```
ROI_1yr = (net_annual - investment) / investment × 100
ROI_3yr = (net_annual × 3 - investment) / investment × 100
Payback_months = investment / (net_annual / 12)
NPV_3yr = net_annual × 3 - investment
```

## Notes
- The standard method is **fixed**; other methodologies are optional tools and
  do not override the main workflow results.
- All formulas and constants are centralized in
  `executors/cost_estimator/formulas.py`.
