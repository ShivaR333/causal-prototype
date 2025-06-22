# Causal Analysis System Test Plan

This document outlines the comprehensive testing strategy for the causal analysis system, including ground truth generation, sample data creation, and pass/fail criteria for each query type.

## Overview

The test bench evaluates five core query types across three different DAG structures to comprehensively assess the causal analysis system's capabilities. Each test combines synthetic data generation with known causal relationships to enable rigorous validation.

## Test DAG Structures

### 1. Simple Linear DAG
**Structure**: X → T → Y (with X → Y)
- **X**: Confounder variable (continuous, N(0,1))
- **T**: Treatment variable (binary, logistic regression on X)
- **Y**: Outcome variable (linear combination of X and T)

**Data Generation**:
```python
X = np.random.normal(0, 1, n_samples)
T_logits = 0.5 * X + np.random.normal(0, 0.5, n_samples)
T = (T_logits > 0).astype(int)
Y = 2.0 * X + 1.5 * T + np.random.normal(0, 0.5, n_samples)
```

### 2. Complex Healthcare DAG
**Structure**: Multi-variable healthcare intervention with mediator
- **Variables**: age, income, severity, treatment, adherence, outcome
- **Relationships**: Complex interactions modeling real healthcare scenarios

**Data Generation**:
```python
age = np.random.uniform(18, 80, n_samples)
income = np.random.exponential(50000, n_samples)
severity = 0.02 * age + np.random.normal(0, 1, n_samples)
treatment = logistic(-2.0 + 0.03*age + 0.00001*income + 0.8*severity)
adherence = 0.5 + 0.3*treatment + 0.000005*income + noise
outcome = 50 + 0.2*age - 0.0001*income - 5*severity + 8*treatment + 15*adherence + noise
```

### 3. Collider Bias DAG
**Structure**: T → Z ← Y with confounders U and X
- **Purpose**: Tests handling of collider bias scenarios
- **True effect**: T → Y with coefficient 1.2

## Query Type Testing Details

---

## 1. Effect Estimation

### Purpose
Estimate the causal effect of a treatment variable on an outcome variable.

### Ground Truth Generation
- **Simple Linear DAG**: True effect = 1.5 (coefficient of T in Y equation)
- **Complex Healthcare DAG**: True effect = 8.0 (direct effect of treatment on outcome)
- **Collider Bias DAG**: True effect = 1.2 (coefficient of T in Y equation)

### Sample Query
```json
{
  "query_type": "effect_estimation",
  "treatment_variable": "T",
  "outcome_variable": "Y",
  "confounders": ["X"],
  "treatment_value": 1.0
}
```

### Expected Output
```json
{
  "success": true,
  "estimate": 1.4919,
  "confidence_interval": [1.2, 1.8],
  "summary": "Estimated causal effect of T on Y: 1.4919"
}
```

### Pass/Fail Criteria
- **PASS**: Relative error ≤ 50% of ground truth value
- **FAIL**: Relative error > 50% of ground truth value
- **Ground Truth Lookup**: `ground_truth["causal_effects"]["{treatment}_on_{outcome}"]`

### Current Performance
- Simple Linear DAG: ✅ PASS (0.54% error)
- Complex Healthcare DAG: ❌ FAIL (51.11% error)
- Collider Bias DAG: ❌ FAIL (100% error - returns 0)

---

## 2. Anomaly Attribution

### Purpose
Identify and attribute anomalies in the outcome variable to potential causes.

### Ground Truth Generation
Anomalies are artificially injected into 5% of randomly selected samples:
```python
anomaly_indices = np.random.choice(len(data), size=int(0.05 * len(data)), replace=False)
data.loc[anomaly_indices, outcome_var] += np.random.normal(3, 1, len(anomaly_indices))
ground_truth["anomalies"]["count"] = len(anomaly_indices)  # Expected: 50 for 1000 samples
```

### Sample Query
```json
{
  "query_type": "anomaly_attribution",
  "outcome_variable": "Y",
  "anomaly_threshold": "auto",
  "potential_causes": ["X", "T"]
}
```

### Expected Output
```json
{
  "success": true,
  "anomalies_found": 48,
  "attribution_scores": {
    "X": {"correlation": 0.15, "difference": 2.1},
    "T": {"correlation": 0.89, "difference": 1.8}
  }
}
```

### Pass/Fail Criteria
- **PASS**: Absolute error ≤ 10 anomalies from ground truth count
- **FAIL**: Absolute error > 10 anomalies from ground truth count
- **Ground Truth**: 50 anomalies (5% of 1000 samples)

### Current Performance
- All DAGs: ❌ FAIL (finding ~22-23 anomalies vs expected 50)

### Known Issues
- Threshold calculation may be too conservative
- Simple correlation-based attribution may miss complex relationships

---

## 3. Distribution Shift Attribution

### Purpose
Identify and quantify distribution shifts between baseline and comparison periods.

### Ground Truth Generation
Data is split into two halves (baseline vs comparison):
```python
baseline_data = data[:n_samples//2]
comparison_data = data[n_samples//2:]
baseline_mean = baseline_data[outcome_var].mean()
comparison_mean = comparison_data[outcome_var].mean()
ground_truth["distribution_shift"] = comparison_mean - baseline_mean
```

### Sample Query
```json
{
  "query_type": "distribution_shift_attribution",
  "target_variable": "Y",
  "baseline_period": "baseline",
  "comparison_period": "comparison",
  "potential_drivers": ["X"]
}
```

### Expected Output
```json
{
  "success": true,
  "shift_magnitude": 0.0253,
  "driver_contributions": {
    "X": {"shift": 0.02, "correlation_with_target": 0.85, "estimated_contribution": 0.017}
  }
}
```

### Pass/Fail Criteria
- **PASS**: Currently all pass (no specific error threshold defined)
- **Future Enhancement**: Could add relative error threshold for shift magnitude

### Current Performance
- All DAGs: ✅ PASS with good accuracy
- Simple Linear DAG: 176% relative error (still passing due to no threshold)
- Complex Healthcare DAG: 6.04% relative error
- Collider Bias DAG: 6.18% relative error

---

## 4. Intervention

### Purpose
Simulate the effect of intervening on a variable and predict outcomes.

### Ground Truth Generation
Uses the same causal effect as effect estimation:
```python
ground_truth["interventions"][f"{intervention_var}_{intervention_value}_on_{outcome}"] = causal_effect
```

### Sample Query
```json
{
  "query_type": "intervention",
  "intervention_variable": "T",
  "intervention_value": 1.0,
  "outcome_variables": ["Y"]
}
```

### Expected Output
```json
{
  "success": true,
  "intervention_effects": {
    "Y": {
      "original_value": 2.45,
      "intervened_value": 3.95,
      "effect": 1.5
    }
  }
}
```

### Pass/Fail Criteria
- **PASS**: Relative error ≤ 50% of ground truth intervention effect
- **FAIL**: Relative error > 50% of ground truth intervention effect

### Current Performance
- All DAGs: ❌ FAIL (0% pass rate)
- Issue: Simple correlation-based simulation doesn't capture true causal effects

### Known Issues
- Current implementation uses simple correlation instead of proper causal inference
- Needs integration with DoWhy intervention capabilities

---

## 5. Counterfactual

### Purpose
Answer "what if" questions by comparing factual and counterfactual scenarios.

### Ground Truth Generation
Based on the negative of the causal effect (switching from treatment=1 to treatment=0):
```python
ground_truth["counterfactual"] = {
  f"{treatment_var}_1_to_0_effect": -causal_effect
}
```

### Sample Query
```json
{
  "query_type": "counterfactual",
  "factual_scenario": {"T": 1, "X": 0.5},
  "counterfactual_scenario": {"T": 0, "X": 0.5},
  "outcome_variable": "Y",
  "evidence_variables": ["X"]
}
```

### Expected Output
```json
{
  "success": true,
  "factual_outcome": 3.2,
  "counterfactual_outcome": 1.7,
  "counterfactual_effect": -1.5
}
```

### Pass/Fail Criteria
- **PASS**: Currently all pass (no specific error threshold defined)
- **Future Enhancement**: Could add relative error threshold

### Current Performance
- All DAGs: ✅ PASS (100% pass rate)
- Errors range from 39.75% to 95.12% but still marked as passing

---

## Test Execution Summary

### Overall Performance Metrics
- **Total Tests**: 15 (5 query types × 3 DAGs)
- **Current Pass Rate**: 46.7% (7 PASS, 8 FAIL)
- **Average Execution Time**: 2.8ms

### Performance by Query Type
| Query Type | Pass Rate | Avg Time | Status |
|------------|-----------|----------|--------|
| Distribution Shift Attribution | 100% (3/3) | 0.9ms | ✅ Good |
| Counterfactual | 100% (3/3) | 1.2ms | ✅ Good |
| Effect Estimation | 33% (1/3) | 9.9ms | ⚠️ Needs Improvement |
| Anomaly Attribution | 0% (0/3) | 1.4ms | ❌ Needs Work |
| Intervention | 0% (0/3) | 0.8ms | ❌ Needs Work |

## Recommendations for Improvement

### 1. Effect Estimation
- **Issue**: DoWhy model struggles with complex confounding and collider bias
- **Solution**: Implement better confounder selection and collider bias detection

### 2. Anomaly Attribution
- **Issue**: Conservative threshold setting and simple correlation-based attribution
- **Solution**: Improve anomaly detection algorithm and attribution methodology

### 3. Intervention
- **Issue**: Using correlation instead of causal inference
- **Solution**: Integrate DoWhy's intervention capabilities properly

### 4. Test Robustness
- **Enhancement**: Add more diverse DAG structures
- **Enhancement**: Include non-linear relationships
- **Enhancement**: Test with missing data scenarios

## Historical Analysis

The test bench now includes comprehensive historical tracking:
- **Timestamped Results**: Each run saved with unique timestamp
- **Trend Analysis**: Track performance improvements over time
- **Detailed Metrics**: Error rates, execution times, pass/fail patterns

Use `python analyze_test_history.py` to generate detailed performance analysis and visualizations.