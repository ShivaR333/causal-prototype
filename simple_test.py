#!/usr/bin/env python3
"""
Simple test to verify the causal analysis system is working.
This runs a minimal test without the full test bench complexity.
"""

import json
import numpy as np
import pandas as pd
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from causal_analysis.dispatch import dispatch_query
    print("✅ Successfully imported dispatch_query")
except ImportError as e:
    print(f"❌ Failed to import dispatch_query: {e}")
    sys.exit(1)

def create_simple_test():
    """Create a simple test case."""
    
    # Create simple DAG
    dag = {
        "name": "simple_test_dag",
        "description": "Simple test DAG",
        "variables": {
            "X": {"name": "confounder", "type": "continuous", "description": "Confounder"},
            "T": {"name": "treatment", "type": "binary", "description": "Treatment"},
            "Y": {"name": "outcome", "type": "continuous", "description": "Outcome"}
        },
        "edges": [
            {"from": "X", "to": "T"},
            {"from": "X", "to": "Y"},
            {"from": "T", "to": "Y"}
        ],
        "treatment_variable": "T",
        "outcome_variable": "Y",
        "confounders": ["X"]
    }
    
    # Create simple data
    np.random.seed(42)
    n = 100
    X = np.random.normal(0, 1, n)
    T = (0.5 * X + np.random.normal(0, 0.5, n) > 0).astype(int)
    Y = 2.0 * X + 1.5 * T + np.random.normal(0, 0.5, n)
    
    data = pd.DataFrame({"X": X, "T": T, "Y": Y})
    
    return dag, data

def run_simple_test():
    """Run a simple test."""
    
    print("🧪 Running Simple Causal Analysis Test")
    print("=" * 40)
    
    try:
        # Create test case
        print("📊 Creating test case...")
        dag, data = create_simple_test()
        
        # Save temporary files
        dag_file = "temp_dag.json"
        data_file = "temp_data.csv"
        
        with open(dag_file, 'w') as f:
            json.dump(dag, f, indent=2)
        data.to_csv(data_file, index=False)
        
        print(f"   - DAG saved to {dag_file}")
        print(f"   - Data saved to {data_file} ({len(data)} rows)")
        
        # Create simple query
        query = {
            "query_type": "effect_estimation",
            "treatment_variable": "T",
            "outcome_variable": "Y",
            "confounders": ["X"]
        }
        
        print(f"⚡ Running query: {query['query_type']}")
        
        # Run the query
        result = dispatch_query(query, dag_file, data_file)
        
        # Check results
        if result.get("success", False):
            print("✅ Query executed successfully!")
            print(f"   - Estimated effect: {result.get('estimate', 'N/A')}")
            print(f"   - Summary: {result.get('summary', 'N/A')}")
            success = True
        else:
            print("❌ Query failed!")
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            success = False
        
        # Clean up
        os.remove(dag_file)
        os.remove(data_file)
        print("🧹 Cleaned up temporary files")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_simple_test()
    
    if success:
        print("\n🎉 Simple test PASSED!")
        print("The causal analysis system is working correctly.")
        print("You can now run the full test bench with: python test_bench.py")
    else:
        print("\n💥 Simple test FAILED!")
        print("Please check the error messages above.")
    
    sys.exit(0 if success else 1)