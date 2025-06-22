#!/usr/bin/env python3
"""
Test script for synthetic data generation functionality.
"""

import pandas as pd
from causal_analysis.data.synthetic_generator import SyntheticDataGenerator
from causal_analysis.data.utils import (
    create_simple_treatment_outcome_dag,
    generate_sample_dataset,
    validate_dataset_for_causal_analysis,
    create_mediation_dag
)

def test_basic_data_generation():
    """Test basic synthetic data generation."""
    print("=== Testing Basic Data Generation ===")
    
    # Generate sample dataset
    data = generate_sample_dataset(
        n_samples=1000,
        treatment_effect=2.5,
        seed=42
    )
    
    print(f"Generated dataset shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print("\nFirst 5 rows:")
    print(data.head())
    
    print("\nDataset summary statistics:")
    print(data.describe())
    
    # Validate dataset
    validation = validate_dataset_for_causal_analysis(
        data, treatment_var="T", outcome_var="Y", confounders=["X"]
    )
    
    print(f"\nDataset validation:")
    print(f"Valid: {validation['valid']}")
    if validation['errors']:
        print(f"Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")

def test_custom_dag():
    """Test data generation with custom DAG."""
    print("\n=== Testing Custom DAG ===")
    
    # Create custom DAG
    dag_config = create_simple_treatment_outcome_dag(
        treatment_name="treatment",
        outcome_name="outcome", 
        confounder_names=["age", "income"]
    )
    
    print(f"DAG variables: {list(dag_config['variables'].keys())}")
    print(f"DAG edges: {dag_config['edges']}")
    
    # Generate data
    generator = SyntheticDataGenerator(dag_config, seed=123)
    data = generator.generate_data(
        n_samples=500,
        treatment_effect=1.8,
        noise_std=0.3
    )
    
    print(f"\nGenerated dataset shape: {data.shape}")
    print("Dataset info:")
    print(data.info())

def test_multiple_datasets():
    """Test generation of multiple datasets with different effects."""
    print("\n=== Testing Multiple Datasets ===")
    
    dag_config = create_simple_treatment_outcome_dag()
    generator = SyntheticDataGenerator(dag_config, seed=456)
    
    datasets = generator.generate_multiple_datasets(
        n_datasets=3,
        n_samples=200,
        treatment_effects=[1.0, 2.0, 3.0]
    )
    
    print(f"Generated {len(datasets)} datasets")
    
    for i, (data, true_effect) in enumerate(datasets):
        print(f"\nDataset {i+1}:")
        print(f"  True treatment effect: {true_effect}")
        print(f"  Shape: {data.shape}")
        
        # Calculate empirical treatment effect (simple difference in means)
        treated = data[data['T'] == 1]['Y']
        control = data[data['T'] == 0]['Y'] 
        empirical_effect = treated.mean() - control.mean()
        print(f"  Empirical effect (unadjusted): {empirical_effect:.3f}")

def test_mediation_dag():
    """Test mediation DAG structure."""
    print("\n=== Testing Mediation DAG ===")
    
    mediation_dag = create_mediation_dag(
        treatment_name="T",
        mediator_name="M",
        outcome_name="Y", 
        confounder_names=["X"]
    )
    
    print(f"Mediation DAG variables: {list(mediation_dag['variables'].keys())}")
    print(f"Edges: {mediation_dag['edges']}")
    
    generator = SyntheticDataGenerator(mediation_dag, seed=789)
    data = generator.generate_data(n_samples=300, treatment_effect=1.5)
    
    print(f"\nMediation dataset shape: {data.shape}")
    print("Correlation matrix:")
    print(data.corr().round(3))

def test_data_summary():
    """Test data summary functionality."""
    print("\n=== Testing Data Summary ===")
    
    generator = SyntheticDataGenerator("causal_analysis/config/sample_dag.json", seed=999)
    data = generator.generate_data(n_samples=100)
    
    summary = generator.get_data_summary(data)
    
    print(f"Data summary:")
    print(f"  Samples: {summary['n_samples']}")
    print(f"  Variables: {summary['n_variables']}")
    
    for var_name, var_info in summary['variables'].items():
        print(f"  {var_name}: mean={var_info['mean']:.3f}, std={var_info['std']:.3f}")

if __name__ == "__main__":
    print("Testing Synthetic Data Generation Module")
    print("=" * 50)
    
    try:
        test_basic_data_generation()
        test_custom_dag()
        test_multiple_datasets() 
        test_mediation_dag()
        test_data_summary()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully! ✅")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()