#!/usr/bin/env python3
"""
Test script to verify causal agent container functionality
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        import networkx as nx
        import dowhy
        import openai
        import causal_eda
        import causal_analysis
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_structure():
    """Test if required files and directories exist"""
    print("Testing file structure...")
    required_files = [
        "causal_agent.py",
        "causal_eda.py",
        "examples/eCommerce_sales_dag.json",
        "sample_data/eCommerce_sales.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_causal_eda():
    """Test CausalEDA functionality"""
    print("Testing CausalEDA...")
    try:
        from causal_eda import CausalEDA
        
        # Test with sample data
        dag_path = "examples/eCommerce_sales_dag.json"
        data_path = "sample_data/eCommerce_sales.csv"
        
        if Path(dag_path).exists() and Path(data_path).exists():
            eda = CausalEDA(
                data_path=data_path,
                dag_path=dag_path,
                output_dir="test_output"
            )
            print("✅ CausalEDA initialized successfully")
            return True
        else:
            print("❌ Required test files not found")
            return False
    except Exception as e:
        print(f"❌ CausalEDA test failed: {e}")
        traceback.print_exc()
        return False

def test_causal_analysis():
    """Test causal analysis dispatch"""
    print("Testing causal analysis dispatch...")
    try:
        from causal_analysis.dispatch import dispatch_query
        print("✅ Causal analysis dispatch imported successfully")
        return True
    except Exception as e:
        print(f"❌ Causal analysis test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running causal agent container tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_file_structure,
        test_causal_eda,
        test_causal_analysis
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Container is ready for use.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()