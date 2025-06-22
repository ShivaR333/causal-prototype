from pydantic import BaseModel
from typing import List, Optional, Union, Literal


class EffectEstimationQuery(BaseModel):
    query_type: Literal["effect_estimation"] = "effect_estimation"
    treatment_variable: str
    outcome_variable: str
    confounders: List[str]
    treatment_value: Optional[float] = None


class AnomalyAttributionQuery(BaseModel):
    query_type: Literal["anomaly_attribution"] = "anomaly_attribution"
    outcome_variable: str
    anomaly_threshold: float
    potential_causes: List[str]
    time_window: Optional[str] = None


class DistributionShiftAttributionQuery(BaseModel):
    query_type: Literal["distribution_shift_attribution"] = "distribution_shift_attribution"
    target_variable: str
    baseline_period: str
    comparison_period: str
    potential_drivers: List[str]


class InterventionQuery(BaseModel):
    query_type: Literal["intervention"] = "intervention"
    intervention_variable: str
    intervention_value: float
    outcome_variables: List[str]
    constraints: Optional[List[str]] = None


class CounterfactualQuery(BaseModel):
    query_type: Literal["counterfactual"] = "counterfactual"
    factual_scenario: dict
    counterfactual_scenario: dict
    outcome_variable: str
    evidence_variables: Optional[List[str]] = None


CausalQuery = Union[
    EffectEstimationQuery,
    AnomalyAttributionQuery, 
    DistributionShiftAttributionQuery,
    InterventionQuery,
    CounterfactualQuery
]