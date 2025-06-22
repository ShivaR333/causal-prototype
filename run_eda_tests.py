#!/usr/bin/env python3
"""
Test runner for Causal EDA Script

This script runs the causal EDA analysis on all available sample datasets
and integrates with the existing test bench framework.

Usage:
    python run_eda_tests.py
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import datetime

# Import the test bench for integration
try:
    from test_bench import CausalTestBench
except ImportError as e:
    print(f"Warning: Could not import test_bench: {e}")
    CausalTestBench = None

def find_sample_datasets() -> List[Dict]:
    """Find all sample datasets in the project."""
    datasets = []
    
    # Common sample data locations
    sample_dirs = ["sample_data", "examples"]
    dag_dirs = [".", "examples"]
    
    for sample_dir in sample_dirs:
        sample_path = Path(sample_dir)
        if sample_path.exists():
            for csv_file in sample_path.glob("*.csv"):
                dataset_info = {
                    "data_path": str(csv_file),
                    "name": csv_file.stem,
                    "dag_path": None
                }
                
                # Look for corresponding DAG file
                for dag_dir in dag_dirs:
                    dag_path = Path(dag_dir)
                    potential_dags = [
                        dag_path / f"{csv_file.stem}_dag.json",
                        dag_path / f"{csv_file.stem}.json",
                        dag_path / "sample_dag.json"
                    ]
                    
                    for dag_file in potential_dags:
                        if dag_file.exists():
                            dataset_info["dag_path"] = str(dag_file)
                            break
                    
                    if dataset_info["dag_path"]:
                        break
                
                datasets.append(dataset_info)
    
    return datasets

def run_eda_analysis(dataset_info: Dict) -> Dict:
    """Run EDA analysis on a single dataset."""
    print(f"\n🔍 Running EDA on: {dataset_info['name']}")
    print("-" * 50)
    
    # Prepare command
    cmd = [
        sys.executable, "causal_eda.py",
        "--data", dataset_info["data_path"],
        "--output", f"eda_output_{dataset_info['name']}"
    ]
    
    if dataset_info["dag_path"]:
        cmd.extend(["--dag", dataset_info["dag_path"]])
        print(f"  📊 Using DAG: {dataset_info['dag_path']}")
    else:
        print(f"  📊 Auto-detecting variables (no DAG provided)")
    
    result = {
        "dataset": dataset_info["name"],
        "data_path": dataset_info["data_path"],
        "dag_path": dataset_info["dag_path"],
        "status": "UNKNOWN",
        "error": None,
        "execution_time": None,
        "output_dir": f"eda_output_{dataset_info['name']}",
        "plots_generated": 0,
        "variables_analyzed": 0
    }
    
    try:
        # Run the EDA script
        import time
        start_time = time.time()
        
        process_result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        execution_time = time.time() - start_time
        result["execution_time"] = execution_time
        
        if process_result.returncode == 0:
            result["status"] = "SUCCESS"
            print(f"  ✅ EDA completed successfully in {execution_time:.2f}s")
            
            # Count generated files
            output_dir = Path(f"eda_output_{dataset_info['name']}")
            if output_dir.exists():
                plots = list(output_dir.glob("*.png"))
                result["plots_generated"] = len(plots)
                print(f"  📊 Generated {len(plots)} plots")
                
                # Try to read variable inventory
                inventory_file = output_dir / "variable_inventory.csv"
                if inventory_file.exists():
                    try:
                        inventory = pd.read_csv(inventory_file)
                        result["variables_analyzed"] = len(inventory)
                        print(f"  📋 Analyzed {len(inventory)} variables")
                    except:
                        pass
        else:
            result["status"] = "FAILED"
            result["error"] = process_result.stderr or "Unknown error"
            print(f"  ❌ EDA failed: {result['error']}")
            
    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["error"] = "Analysis timed out after 5 minutes"
        print(f"  ⏰ EDA timed out")
        
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        print(f"  💥 EDA error: {e}")
    
    return result

def generate_eda_test_report(results: List[Dict]) -> str:
    """Generate a comprehensive test report for EDA runs."""
    
    report = []
    report.append("🧪 CAUSAL EDA TEST REPORT")
    report.append("=" * 50)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary statistics
    total_tests = len(results)
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    timeouts = sum(1 for r in results if r["status"] == "TIMEOUT")
    
    report.append(f"📊 SUMMARY:")
    report.append(f"  Total datasets tested: {total_tests}")
    report.append(f"  Successful: {successful} ({successful/total_tests*100:.1f}%)")
    report.append(f"  Failed: {failed} ({failed/total_tests*100:.1f}%)")
    report.append(f"  Errors: {errors} ({errors/total_tests*100:.1f}%)")
    report.append(f"  Timeouts: {timeouts} ({timeouts/total_tests*100:.1f}%)")
    report.append("")
    
    # Detailed results
    report.append("📋 DETAILED RESULTS:")
    report.append("-" * 30)
    
    for result in results:
        status_emoji = {
            "SUCCESS": "✅",
            "FAILED": "❌", 
            "ERROR": "💥",
            "TIMEOUT": "⏰",
            "UNKNOWN": "❓"
        }.get(result["status"], "❓")
        
        report.append(f"\n{status_emoji} {result['dataset']}")
        report.append(f"   Data: {result['data_path']}")
        if result["dag_path"]:
            report.append(f"   DAG: {result['dag_path']}")
        report.append(f"   Status: {result['status']}")
        
        if result["execution_time"]:
            report.append(f"   Time: {result['execution_time']:.2f}s")
        
        if result["plots_generated"] > 0:
            report.append(f"   Plots: {result['plots_generated']}")
            
        if result["variables_analyzed"] > 0:
            report.append(f"   Variables: {result['variables_analyzed']}")
        
        if result["error"]:
            report.append(f"   Error: {result['error']}")
    
    # Performance analysis
    successful_results = [r for r in results if r["status"] == "SUCCESS"]
    if successful_results:
        avg_time = sum(r["execution_time"] for r in successful_results) / len(successful_results)
        total_plots = sum(r["plots_generated"] for r in successful_results)
        total_variables = sum(r["variables_analyzed"] for r in successful_results)
        
        report.append(f"\n📈 PERFORMANCE ANALYSIS:")
        report.append(f"  Average execution time: {avg_time:.2f}s")
        report.append(f"  Total plots generated: {total_plots}")
        report.append(f"  Total variables analyzed: {total_variables}")
    
    # Recommendations
    report.append(f"\n💡 RECOMMENDATIONS:")
    
    if successful / total_tests >= 0.8:
        report.append("  🎉 EDA script is working well across datasets!")
    elif successful / total_tests >= 0.6:
        report.append("  ⚠️  EDA script has some issues - review failed cases")
    else:
        report.append("  ❌ EDA script needs significant improvements")
    
    if timeouts > 0:
        report.append("  ⏰ Consider optimizing for large datasets (timeouts detected)")
    
    if errors > 0:
        report.append("  🐛 Debug error cases for improved robustness")
    
    return "\n".join(report)

def integrate_with_test_bench(eda_results: List[Dict]) -> None:
    """Integrate EDA results with the existing test bench."""
    if not CausalTestBench:
        print("⚠️  Test bench integration not available")
        return
    
    print("\n🔗 Integrating with test bench...")
    
    try:
        # Create test bench
        test_bench = CausalTestBench(output_dir="test_results")
        
        # Add EDA results to test bench results
        eda_test_results = []
        
        for eda_result in eda_results:
            test_result = {
                "dag_name": f"eda_{eda_result['dataset']}",
                "query_type": "exploratory_data_analysis",
                "status": "PASS" if eda_result["status"] == "SUCCESS" else "FAIL",
                "error": eda_result["error"],
                "estimated_value": eda_result["plots_generated"],
                "ground_truth_value": "N/A",
                "absolute_error": None,
                "relative_error": None,
                "execution_time": eda_result["execution_time"],
                "test_id": f"eda_{eda_result['dataset']}"
            }
            eda_test_results.append(test_result)
        
        # Save EDA test results
        eda_results_file = Path("test_results") / "eda_test_results.json"
        with open(eda_results_file, 'w') as f:
            json.dump(eda_test_results, f, indent=2, default=str)
        
        print(f"  ✅ EDA results integrated and saved to: {eda_results_file}")
        
    except Exception as e:
        print(f"  ❌ Integration failed: {e}")

def main():
    """Main function to run EDA tests."""
    print("🧪 CAUSAL EDA TEST RUNNER")
    print("=" * 40)
    
    # Find datasets
    print("🔍 Discovering sample datasets...")
    datasets = find_sample_datasets()
    
    if not datasets:
        print("❌ No sample datasets found!")
        print("   Make sure you have CSV files in 'sample_data' or 'examples' directories")
        return 1
    
    print(f"✅ Found {len(datasets)} datasets:")
    for dataset in datasets:
        dag_status = "with DAG" if dataset["dag_path"] else "no DAG"
        print(f"  • {dataset['name']} ({dag_status})")
    
    # Run EDA on all datasets
    print(f"\n🚀 Running EDA analysis on {len(datasets)} datasets...")
    print("=" * 60)
    
    results = []
    for i, dataset in enumerate(datasets, 1):
        print(f"\n[{i}/{len(datasets)}] Processing: {dataset['name']}")
        result = run_eda_analysis(dataset)
        results.append(result)
    
    # Generate report
    print(f"\n📊 Generating test report...")
    report = generate_eda_test_report(results)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path("test_results")
    report_file.mkdir(exist_ok=True)
    
    current_report = report_file / "eda_test_report.txt"
    timestamped_report = report_file / f"eda_test_report_{timestamp}.txt"
    
    with open(current_report, 'w') as f:
        f.write(report)
    
    with open(timestamped_report, 'w') as f:
        f.write(report)
    
    # Save results as JSON
    results_json = report_file / "eda_test_results.json"
    with open(results_json, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(report)
    
    print(f"\n📄 Report saved to: {current_report}")
    print(f"📊 Results saved to: {results_json}")
    
    # Integrate with test bench
    integrate_with_test_bench(results)
    
    # Return appropriate exit code
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    success_rate = successful / len(results) if results else 0
    
    if success_rate >= 0.8:
        print(f"\n🎉 EDA testing PASSED! ({success_rate:.1%} success rate)")
        return 0
    elif success_rate >= 0.6:
        print(f"\n⚠️  EDA testing PARTIAL ({success_rate:.1%} success rate)")
        return 1
    else:
        print(f"\n❌ EDA testing FAILED ({success_rate:.1%} success rate)")
        return 2

if __name__ == "__main__":
    exit(main())