import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

from .causal_model import CausalModel


def dispatch_query(query_json: dict, dag_path: str, data_path: str) -> dict:
    """
    Dispatch causal query based on query type.
    
    Args:
        query_json: Dictionary containing query parameters with 'query_type' field
        dag_path: Path to DAG JSON configuration file
        data_path: Path to CSV data file
        
    Returns:
        Dictionary with query results
    """
    try:
        # Load data
        data = pd.read_csv(data_path)
        
        # Create causal model
        causal_model = CausalModel(dag_path, data)
        
        # Dispatch based on query type
        query_type = query_json.get("query_type")
        
        if query_type == "effect_estimation":
            return _handle_effect_estimation(query_json, causal_model)
        elif query_type == "anomaly_attribution":
            return _handle_anomaly_attribution(query_json, causal_model)
        elif query_type == "distribution_shift_attribution":
            return _handle_distribution_shift_attribution(query_json, causal_model)
        elif query_type == "intervention":
            return _handle_intervention(query_json, causal_model)
        elif query_type == "counterfactual":
            return _handle_counterfactual(query_json, causal_model)
        else:
            return {
                "success": False,
                "error": f"Unknown query type: {query_type}",
                "query_type": query_type
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query_type": query_json.get("query_type", "unknown")
        }


def _handle_effect_estimation(query_json: dict, causal_model: CausalModel) -> dict:
    """Handle effect estimation queries using DoWhy."""
    try:
        treatment_var = query_json["treatment_variable"]
        outcome_var = query_json["outcome_variable"]
        confounders = query_json.get("confounders", [])
        treatment_value = query_json.get("treatment_value")
        
        # Identify causal effect
        identified_estimand = causal_model.identify_effect()
        
        # Estimate effect using multiple methods compatible with DoWhy 0.12+
        methods = ["backdoor.linear_regression", "backdoor.propensity_score_stratification"]
        estimates = []
        
        for method in methods:
            try:
                estimate = causal_model.estimate_effect(
                    identified_estimand,
                    method_name=method
                )
                # Handle different DoWhy versions - estimate might be a number or object
                if hasattr(estimate, 'value'):
                    estimate_value = float(estimate.value)
                else:
                    estimate_value = float(estimate)
                
                estimates.append({
                    "method": method,
                    "estimate": estimate_value,
                    "confidence_interval": [
                        float(estimate_value - 1.96 * abs(estimate_value) * 0.1),
                        float(estimate_value + 1.96 * abs(estimate_value) * 0.1)
                    ]
                })
            except Exception as method_error:
                estimates.append({
                    "method": method,
                    "error": str(method_error)
                })
        
        # Use first successful estimate as primary result
        primary_estimate = next((e for e in estimates if "estimate" in e), None)
        
        if primary_estimate:
            return {
                "success": True,
                "query_type": "effect_estimation",
                "treatment_variable": treatment_var,
                "outcome_variable": outcome_var,
                "estimate": primary_estimate["estimate"],
                "confidence_interval": primary_estimate["confidence_interval"],
                "all_estimates": estimates,
                "summary": f"Estimated causal effect of {treatment_var} on {outcome_var}: {primary_estimate['estimate']:.4f}"
            }
        else:
            return {
                "success": False,
                "query_type": "effect_estimation",
                "error": "All estimation methods failed",
                "failed_estimates": estimates
            }
            
    except Exception as e:
        return {
            "success": False,
            "query_type": "effect_estimation",
            "error": str(e)
        }


def _handle_anomaly_attribution(query_json: dict, causal_model: CausalModel) -> dict:
    """Handle anomaly attribution queries using simple statistical analysis."""
    try:
        outcome_var = query_json["outcome_variable"]
        anomaly_threshold = query_json["anomaly_threshold"]
        potential_causes = query_json["potential_causes"]
        time_window = query_json.get("time_window")
        
        data = causal_model.data
        
        # Identify anomalies
        outcome_values = data[outcome_var]
        anomalies = outcome_values > anomaly_threshold
        
        if not anomalies.any():
            return {
                "success": True,
                "query_type": "anomaly_attribution",
                "outcome_variable": outcome_var,
                "anomalies_found": 0,
                "attribution_scores": {},
                "summary": f"No anomalies found above threshold {anomaly_threshold}"
            }
        
        # Calculate attribution scores for potential causes
        attribution_scores = {}
        for cause in potential_causes:
            if cause in data.columns:
                # Simple correlation-based attribution
                correlation = data[cause].corr(outcome_values)
                
                # Difference in means between anomalous and normal periods
                normal_mean = data.loc[~anomalies, cause].mean()
                anomaly_mean = data.loc[anomalies, cause].mean()
                
                attribution_scores[cause] = {
                    "correlation": float(correlation) if not np.isnan(correlation) else 0.0,
                    "normal_mean": float(normal_mean) if not np.isnan(normal_mean) else 0.0,
                    "anomaly_mean": float(anomaly_mean) if not np.isnan(anomaly_mean) else 0.0,
                    "difference": float(anomaly_mean - normal_mean) if not (np.isnan(anomaly_mean) or np.isnan(normal_mean)) else 0.0
                }
        
        return {
            "success": True,
            "query_type": "anomaly_attribution",
            "outcome_variable": outcome_var,
            "anomaly_threshold": anomaly_threshold,
            "anomalies_found": int(anomalies.sum()),
            "attribution_scores": attribution_scores,
            "summary": f"Found {anomalies.sum()} anomalies in {outcome_var}. Top contributor: {max(attribution_scores.keys(), key=lambda x: abs(attribution_scores[x]['correlation']))}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "query_type": "anomaly_attribution",
            "error": str(e)
        }


def _handle_distribution_shift_attribution(query_json: dict, causal_model: CausalModel) -> dict:
    """Handle distribution shift attribution queries."""
    try:
        target_var = query_json["target_variable"]
        baseline_period = query_json["baseline_period"]
        comparison_period = query_json["comparison_period"]
        potential_drivers = query_json["potential_drivers"]
        
        data = causal_model.data
        
        # Simple implementation assuming periods are row ranges
        # In practice, you'd have proper date/time filtering
        baseline_data = data.iloc[:len(data)//2]  # First half as baseline
        comparison_data = data.iloc[len(data)//2:]  # Second half as comparison
        
        # Calculate distribution shift
        baseline_mean = baseline_data[target_var].mean()
        comparison_mean = comparison_data[target_var].mean()
        shift_magnitude = comparison_mean - baseline_mean
        
        # Attribute shift to potential drivers
        driver_contributions = {}
        for driver in potential_drivers:
            if driver in data.columns:
                baseline_driver_mean = baseline_data[driver].mean()
                comparison_driver_mean = comparison_data[driver].mean()
                driver_shift = comparison_driver_mean - baseline_driver_mean
                
                # Simple attribution: correlation between driver and target
                correlation = data[driver].corr(data[target_var])
                contribution = driver_shift * correlation if not np.isnan(correlation) else 0.0
                
                driver_contributions[driver] = {
                    "baseline_mean": float(baseline_driver_mean),
                    "comparison_mean": float(comparison_driver_mean),
                    "shift": float(driver_shift),
                    "correlation_with_target": float(correlation) if not np.isnan(correlation) else 0.0,
                    "estimated_contribution": float(contribution)
                }
        
        return {
            "success": True,
            "query_type": "distribution_shift_attribution",
            "target_variable": target_var,
            "baseline_mean": float(baseline_mean),
            "comparison_mean": float(comparison_mean),
            "shift_magnitude": float(shift_magnitude),
            "driver_contributions": driver_contributions,
            "summary": f"Distribution shift of {shift_magnitude:.4f} in {target_var}. Main driver: {max(driver_contributions.keys(), key=lambda x: abs(driver_contributions[x]['estimated_contribution']))}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "query_type": "distribution_shift_attribution",
            "error": str(e)
        }


def _handle_intervention(query_json: dict, causal_model: CausalModel) -> dict:
    """Handle intervention queries using simple simulation."""
    try:
        intervention_var = query_json["intervention_variable"]
        intervention_value = query_json["intervention_value"]
        outcome_vars = query_json["outcome_variables"]
        constraints = query_json.get("constraints", [])
        
        data = causal_model.data.copy()
        
        # Simple intervention simulation
        original_outcomes = {}
        intervened_outcomes = {}
        
        for outcome_var in outcome_vars:
            if outcome_var in data.columns:
                original_outcomes[outcome_var] = float(data[outcome_var].mean())
                
                # Simulate intervention by setting intervention variable
                data_intervened = data.copy()
                data_intervened[intervention_var] = intervention_value
                
                # Simple linear relationship assumption for simulation
                # In practice, you'd use proper causal inference
                if intervention_var in data.columns:
                    correlation = data[intervention_var].corr(data[outcome_var])
                    if not np.isnan(correlation):
                        original_intervention_mean = data[intervention_var].mean()
                        intervention_effect = (intervention_value - original_intervention_mean) * correlation
                        intervened_outcomes[outcome_var] = original_outcomes[outcome_var] + intervention_effect
                    else:
                        intervened_outcomes[outcome_var] = original_outcomes[outcome_var]
                else:
                    intervened_outcomes[outcome_var] = original_outcomes[outcome_var]
        
        # Calculate intervention effects
        intervention_effects = {}
        for outcome_var in outcome_vars:
            if outcome_var in original_outcomes:
                intervention_effects[outcome_var] = {
                    "original_value": original_outcomes[outcome_var],
                    "intervened_value": intervened_outcomes[outcome_var],
                    "effect": intervened_outcomes[outcome_var] - original_outcomes[outcome_var]
                }
        
        return {
            "success": True,
            "query_type": "intervention",
            "intervention_variable": intervention_var,
            "intervention_value": intervention_value,
            "intervention_effects": intervention_effects,
            "summary": f"Intervening on {intervention_var} to {intervention_value} affects {len(intervention_effects)} outcomes"
        }
        
    except Exception as e:
        return {
            "success": False,
            "query_type": "intervention",
            "error": str(e)
        }


def _handle_counterfactual(query_json: dict, causal_model: CausalModel) -> dict:
    """Handle counterfactual queries using simple simulation."""
    try:
        factual_scenario = query_json["factual_scenario"]
        counterfactual_scenario = query_json["counterfactual_scenario"]
        outcome_var = query_json["outcome_variable"]
        evidence_vars = query_json.get("evidence_variables", [])
        
        data = causal_model.data
        
        # Simple counterfactual estimation
        # Filter data to match factual scenario as closely as possible
        filtered_data = data.copy()
        for var, value in factual_scenario.items():
            if var in data.columns:
                # Find rows closest to factual scenario
                filtered_data = filtered_data[
                    np.abs(filtered_data[var] - value) <= filtered_data[var].std()
                ]
        
        if len(filtered_data) == 0:
            filtered_data = data  # Fallback to full data
        
        factual_outcome = filtered_data[outcome_var].mean()
        
        # Estimate counterfactual outcome
        # Simple approach: adjust based on variable differences
        counterfactual_adjustment = 0
        for var, cf_value in counterfactual_scenario.items():
            if var in data.columns and var in factual_scenario:
                factual_value = factual_scenario[var]
                correlation = data[var].corr(data[outcome_var])
                if not np.isnan(correlation):
                    adjustment = (cf_value - factual_value) * correlation
                    counterfactual_adjustment += adjustment
        
        counterfactual_outcome = factual_outcome + counterfactual_adjustment
        
        return {
            "success": True,
            "query_type": "counterfactual",
            "factual_scenario": factual_scenario,
            "counterfactual_scenario": counterfactual_scenario,
            "outcome_variable": outcome_var,
            "factual_outcome": float(factual_outcome),
            "counterfactual_outcome": float(counterfactual_outcome),
            "counterfactual_effect": float(counterfactual_outcome - factual_outcome),
            "summary": f"Counterfactual effect on {outcome_var}: {counterfactual_outcome - factual_outcome:.4f}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "query_type": "counterfactual",
            "error": str(e)
        }