#!/usr/bin/env python3
"""
Command-line tool to generate synthetic data from JSON DAG configuration.
"""

import argparse
import json
from pathlib import Path
from causal_analysis.data.synthetic_generator import SyntheticDataGenerator

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic data from JSON DAG configuration')
    parser.add_argument('dag_file', help='Path to JSON DAG configuration file')
    parser.add_argument('--output', '-o', default='generated_data.csv', help='Output CSV file path')
    parser.add_argument('--samples', '-n', type=int, default=1000, help='Number of samples to generate')
    parser.add_argument('--effect', '-e', type=float, default=2.0, help='Treatment effect size')
    parser.add_argument('--noise', type=float, default=0.5, help='Noise standard deviation')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--summary', action='store_true', help='Print data summary')
    
    args = parser.parse_args()
    
    try:
        # Load DAG configuration
        print(f"Loading DAG configuration from: {args.dag_file}")
        generator = SyntheticDataGenerator(args.dag_file, seed=args.seed)
        
        # Generate data
        print(f"Generating {args.samples} samples with treatment effect {args.effect}...")
        data = generator.generate_data(
            n_samples=args.samples,
            treatment_effect=args.effect,
            noise_std=args.noise
        )
        
        # Save data
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(args.output, index=False)
        print(f"Data saved to: {args.output}")
        
        # Print summary if requested
        if args.summary:
            print("\n=== Data Summary ===")
            summary = generator.get_data_summary(data)
            print(f"Samples: {summary['n_samples']}")
            print(f"Variables: {summary['n_variables']}")
            
            for var_name, var_info in summary['variables'].items():
                print(f"{var_name}: mean={var_info['mean']:.3f}, std={var_info['std']:.3f}, "
                      f"range=[{var_info['min']:.3f}, {var_info['max']:.3f}]")
        
        print("✅ Data generation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())