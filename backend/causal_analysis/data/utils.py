import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from .synthetic_generator import SyntheticDataGenerator

def create_simple_treatment_outcome_dag(
    treatment_name: str = "T",
    outcome_name: str = "Y", 
    confounder_names: List[str] = ["X"]
) -> Dict:
    """
    Create a simple DAG configuration for treatment-outcome analysis.
    
    Args:
        treatment_name: Name of treatment variable
        outcome_name: Name of outcome variable  
        confounder_names: List of confounder variable names
        
    Returns:
        DAG configuration dictionary
    """
    variables = {
        treatment_name: {
            "name": "treatment",
            "type": "binary",
            "description": "Treatment assignment"
        },
        outcome_name: {
            "name": "outcome", 
            "type": "continuous",
            "description": "Outcome variable"
        }
    }
    
    # Add confounders
    for i, conf_name in enumerate(confounder_names):
        variables[conf_name] = {
            "name": f"confounder_{i+1}",
            "type": "continuous", 
            "description": f"Confounder variable {i+1}"
        }
    
    # Create edges: confounders -> treatment, confounders -> outcome, treatment -> outcome
    edges = []
    
    # Confounders affect both treatment and outcome
    for conf_name in confounder_names:
        edges.append({"from": conf_name, "to": treatment_name})
        edges.append({"from": conf_name, "to": outcome_name})
    
    # Treatment affects outcome
    edges.append({"from": treatment_name, "to": outcome_name})
    
    return {
        "name": "simple_treatment_outcome_dag",
        "description": "Simple DAG for treatment effect analysis",
        "variables": variables,
        "edges": edges,
        "treatment_variable": treatment_name,
        "outcome_variable": outcome_name,
        "confounders": confounder_names
    }

def generate_sample_dataset(
    n_samples: int = 1000,
    treatment_effect: float = 2.0,
    dag_config: Optional[Dict] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Quick function to generate a sample dataset.
    
    Args:
        n_samples: Number of samples
        treatment_effect: True causal effect
        dag_config: DAG configuration (uses default if None)
        seed: Random seed
        
    Returns:
        Generated dataset
    """
    if dag_config is None:
        dag_config = create_simple_treatment_outcome_dag()
    
    generator = SyntheticDataGenerator(dag_config, seed=seed)
    return generator.generate_data(
        n_samples=n_samples,
        treatment_effect=treatment_effect
    )

def validate_dataset_for_causal_analysis(
    data: pd.DataFrame,
    treatment_var: str,
    outcome_var: str,
    confounders: List[str]
) -> Dict[str, Union[bool, str, List[str]]]:
    """
    Validate that dataset is suitable for causal analysis.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check if required columns exist
    required_cols = [treatment_var, outcome_var] + confounders
    missing_cols = [col for col in required_cols if col not in data.columns]
    
    if missing_cols:
        results["valid"] = False
        results["errors"].append(f"Missing columns: {missing_cols}")
    
    # Check for sufficient sample size
    if len(data) < 100:
        results["warnings"].append("Sample size is quite small (< 100)")
    
    # Check treatment variable
    if treatment_var in data.columns:
        treatment_unique = data[treatment_var].nunique()
        if treatment_unique < 2:
            results["valid"] = False
            results["errors"].append("Treatment variable has insufficient variation")
        elif treatment_unique > 10:
            results["warnings"].append("Treatment variable has many unique values - consider if this is continuous")
    
    # Check for missing values
    missing_pct = data.isnull().sum() / len(data) * 100
    high_missing = missing_pct[missing_pct > 10]
    
    if len(high_missing) > 0:
        results["warnings"].append(f"High missing values in: {high_missing.to_dict()}")
    
    # Check for overlap in treatment groups (if binary)
    if treatment_var in data.columns and data[treatment_var].nunique() == 2:
        treatment_counts = data[treatment_var].value_counts()
        min_group_size = treatment_counts.min()
        
        if min_group_size < 10:
            results["warnings"].append(f"Small treatment group size: {min_group_size}")
    
    return results

def add_noise_to_dataset(
    data: pd.DataFrame,
    noise_level: float = 0.1,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Add random noise to dataset columns.
    
    Args:
        data: Input dataset
        noise_level: Standard deviation of noise relative to variable std
        columns: Columns to add noise to (all numeric columns if None)
        
    Returns:
        Dataset with added noise
    """
    data_noisy = data.copy()
    
    if columns is None:
        columns = data.select_dtypes(include=[np.number]).columns.tolist()
    
    np.random.seed(42)
    
    for col in columns:
        if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
            col_std = data[col].std()
            noise = np.random.normal(0, noise_level * col_std, len(data))
            data_noisy[col] = data[col] + noise
    
    return data_noisy

def create_mediation_dag(
    treatment_name: str = "T",
    mediator_name: str = "M", 
    outcome_name: str = "Y",
    confounder_names: List[str] = ["X"]
) -> Dict:
    """
    Create DAG configuration for mediation analysis.
    
    Structure: X -> T -> M -> Y, X -> Y, X -> M
    """
    variables = {
        treatment_name: {"name": "treatment", "type": "binary"},
        mediator_name: {"name": "mediator", "type": "continuous"},
        outcome_name: {"name": "outcome", "type": "continuous"}
    }
    
    for i, conf_name in enumerate(confounder_names):
        variables[conf_name] = {
            "name": f"confounder_{i+1}",
            "type": "continuous"
        }
    
    edges = []
    
    # Confounders affect treatment, mediator, and outcome
    for conf_name in confounder_names:
        edges.extend([
            {"from": conf_name, "to": treatment_name},
            {"from": conf_name, "to": mediator_name},
            {"from": conf_name, "to": outcome_name}
        ])
    
    # Causal chain: T -> M -> Y
    edges.extend([
        {"from": treatment_name, "to": mediator_name},
        {"from": mediator_name, "to": outcome_name},
        {"from": treatment_name, "to": outcome_name}  # Direct effect
    ])
    
    return {
        "name": "mediation_dag",
        "variables": variables,
        "edges": edges,
        "treatment_variable": treatment_name,
        "outcome_variable": outcome_name,
        "confounders": confounder_names,
        "mediator": mediator_name
    }