#!/usr/bin/env python3
"""
Examples of how to provide DAG configurations in JSON format.
"""

import json
from causal_analysis.data.synthetic_generator import SyntheticDataGenerator

# Example 1: Create JSON DAG configuration as dictionary
def create_custom_dag_dict():
    """Create a custom DAG configuration as a dictionary."""
    
    custom_dag = {
        "name": "my_custom_dag",
        "description": "Custom DAG with multiple confounders",
        "variables": {
            "age": {
                "name": "age",
                "type": "continuous",
                "description": "Patient age"
            },
            "income": {
                "name": "income", 
                "type": "continuous",
                "description": "Household income"
            },
            "education": {
                "name": "education",
                "type": "categorical", 
                "description": "Education level"
            },
            "treatment": {
                "name": "treatment",
                "type": "binary",
                "description": "Medical treatment (0/1)"
            },
            "outcome": {
                "name": "outcome",
                "type": "continuous", 
                "description": "Health outcome score"
            }
        },
        "edges": [
            {"from": "age", "to": "treatment"},
            {"from": "age", "to": "outcome"},
            {"from": "income", "to": "treatment"},
            {"from": "income", "to": "outcome"},
            {"from": "education", "to": "treatment"},
            {"from": "education", "to": "outcome"},
            {"from": "treatment", "to": "outcome"}
        ],
        "treatment_variable": "treatment",
        "outcome_variable": "outcome",
        "confounders": ["age", "income", "education"]
    }
    
    return custom_dag

# Example 2: Save DAG to JSON file and load it
def save_and_load_dag():
    """Save DAG configuration to JSON file and load it."""
    
    # Create DAG configuration
    dag_config = create_custom_dag_dict()
    
    # Save to JSON file
    with open("my_custom_dag.json", "w") as f:
        json.dump(dag_config, f, indent=2)
    
    print("DAG configuration saved to 'my_custom_dag.json'")
    
    # Load from JSON file and generate data
    generator = SyntheticDataGenerator("my_custom_dag.json", seed=42)
    data = generator.generate_data(n_samples=500, treatment_effect=2.5)
    
    print(f"Generated data shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    
    return data

# Example 3: Complex DAG with instrumental variable
def create_instrumental_variable_dag():
    """Create DAG with instrumental variable structure."""
    
    iv_dag = {
        "name": "instrumental_variable_dag",
        "description": "DAG with instrumental variable",
        "variables": {
            "Z": {
                "name": "instrument",
                "type": "binary",
                "description": "Instrumental variable (e.g., randomized encouragement)"
            },
            "X": {
                "name": "confounder",
                "type": "continuous", 
                "description": "Unobserved confounder"
            },
            "T": {
                "name": "treatment",
                "type": "binary",
                "description": "Treatment received"
            },
            "Y": {
                "name": "outcome",
                "type": "continuous",
                "description": "Outcome of interest"
            }
        },
        "edges": [
            {"from": "Z", "to": "T"},  # Instrument affects treatment
            {"from": "X", "to": "T"},  # Confounder affects treatment  
            {"from": "X", "to": "Y"},  # Confounder affects outcome
            {"from": "T", "to": "Y"}   # Treatment affects outcome
            # Note: Z does not directly affect Y (exclusion restriction)
        ],
        "treatment_variable": "T",
        "outcome_variable": "Y", 
        "confounders": ["X"],
        "instrument": "Z"
    }
    
    return iv_dag

# Example 4: Using the DAG configurations
def demonstrate_usage():
    """Demonstrate different ways to use JSON DAG configurations."""
    
    print("=== Example 1: Using Dictionary Configuration ===")
    dag_dict = create_custom_dag_dict()
    generator1 = SyntheticDataGenerator(dag_dict, seed=123)
    data1 = generator1.generate_data(n_samples=300)
    print(f"Data shape: {data1.shape}")
    print("Columns:", list(data1.columns))
    
    print("\n=== Example 2: Loading from JSON File ===")
    data2 = save_and_load_dag()
    
    print("\n=== Example 3: Instrumental Variable DAG ===")
    iv_dag = create_instrumental_variable_dag()
    
    # Save IV DAG to file
    with open("iv_dag.json", "w") as f:
        json.dump(iv_dag, f, indent=2)
    
    generator3 = SyntheticDataGenerator("iv_dag.json", seed=456)
    data3 = generator3.generate_data(n_samples=400, treatment_effect=1.8)
    print(f"IV Data shape: {data3.shape}")
    print("IV Columns:", list(data3.columns))
    
    # Show correlations to verify IV structure
    print("\nCorrelation matrix (should show Z->T but not Z->Y directly):")
    print(data3.corr().round(3))

if __name__ == "__main__":
    demonstrate_usage()