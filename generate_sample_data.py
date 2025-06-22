#!/usr/bin/env python3
"""
Generate sample datasets for testing the causal analysis pipeline.
"""

import os
from causal_analysis.data.utils import generate_sample_dataset

def main():
    """Generate and save sample datasets."""
    
    # Create data directory if it doesn't exist
    os.makedirs("sample_data", exist_ok=True)
    
    # Generate different datasets
    datasets = [
        {
            "name": "small_effect",
            "n_samples": 1000,
            "treatment_effect": 0.5,
            "description": "Dataset with small treatment effect"
        },
        {
            "name": "medium_effect", 
            "n_samples": 1000,
            "treatment_effect": 2.0,
            "description": "Dataset with medium treatment effect"
        },
        {
            "name": "large_effect",
            "n_samples": 1000, 
            "treatment_effect": 4.0,
            "description": "Dataset with large treatment effect"
        },
        {
            "name": "small_sample",
            "n_samples": 200,
            "treatment_effect": 2.0,
            "description": "Small sample dataset"
        }
    ]
    
    print("Generating sample datasets...")
    
    for dataset_config in datasets:
        print(f"Generating {dataset_config['name']}...")
        
        # Generate data
        data = generate_sample_dataset(
            n_samples=dataset_config["n_samples"],
            treatment_effect=dataset_config["treatment_effect"],
            seed=42
        )
        
        # Save to CSV
        filename = f"sample_data/{dataset_config['name']}.csv"
        data.to_csv(filename, index=False)
        
        print(f"  Saved to {filename}")
        print(f"  Description: {dataset_config['description']}")
        print(f"  Shape: {data.shape}")
        print(f"  Treatment effect: {dataset_config['treatment_effect']}")
        
        # Calculate simple empirical effect
        treated_mean = data[data['T'] == 1]['Y'].mean()
        control_mean = data[data['T'] == 0]['Y'].mean()
        empirical_effect = treated_mean - control_mean
        print(f"  Empirical effect (unadjusted): {empirical_effect:.3f}")
        print()
    
    print("Sample datasets generated successfully!")
    print("Files saved in the 'sample_data' directory.")

if __name__ == "__main__":
    main()