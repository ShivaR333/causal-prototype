#!/usr/bin/env python3
"""
Comprehensive Test Bench for Causal Analysis System

This script:
1. Generates sample DAGs in JSON format
2. Generates sample queries for each query type
3. Generates synthetic data with known ground truth
4. Runs causal analysis using the dispatch system
5. Validates results against ground truth
6. Provides results in tabular format
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
import tempfile
import os
import traceback
import sys
from datetime import datetime

# Try to import tabulate, install if not available
try:
    from tabulate import tabulate
except ImportError:
    print("Installing required dependency: tabulate")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
    from tabulate import tabulate

# Import our causal analysis components
try:
    from causal_analysis.dispatch import dispatch_query
    from causal_analysis.causal_model import CausalModel
except ImportError as e:
    print(f"Error importing causal analysis components: {e}")
    print("Make sure you're running from the project root directory")
    print("Try: python -m test_bench")
    sys.exit(1)


class CausalTestBench:
    """Comprehensive test bench for causal analysis system."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def generate_sample_dags(self) -> List[Dict]:
        """Generate various sample DAGs for testing."""
        
        # Simple Linear DAG: X -> T -> Y
        simple_dag = {
            "name": "simple_linear_dag",
            "description": "Simple linear causal chain",
            "variables": {
                "X": {"name": "confounder", "type": "continuous", "description": "Confounder variable"},
                "T": {"name": "treatment", "type": "binary", "description": "Treatment variable"},
                "Y": {"name": "outcome", "type": "continuous", "description": "Outcome variable"}
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
        
        # Complex DAG: Multiple confounders and mediator
        complex_dag = {
            "name": "complex_healthcare_dag",
            "description": "Complex healthcare intervention with mediator",
            "variables": {
                "age": {"name": "age", "type": "continuous", "description": "Patient age"},
                "income": {"name": "income", "type": "continuous", "description": "Income level"},
                "severity": {"name": "severity", "type": "continuous", "description": "Disease severity"},
                "treatment": {"name": "treatment", "type": "binary", "description": "Treatment received"},
                "adherence": {"name": "adherence", "type": "continuous", "description": "Treatment adherence"},
                "outcome": {"name": "outcome", "type": "continuous", "description": "Health outcome"}
            },
            "edges": [
                {"from": "age", "to": "severity"},
                {"from": "age", "to": "treatment"},
                {"from": "age", "to": "outcome"},
                {"from": "income", "to": "treatment"},
                {"from": "income", "to": "adherence"},
                {"from": "severity", "to": "treatment"},
                {"from": "severity", "to": "outcome"},
                {"from": "treatment", "to": "adherence"},
                {"from": "treatment", "to": "outcome"},
                {"from": "adherence", "to": "outcome"}
            ],
            "treatment_variable": "treatment",
            "outcome_variable": "outcome",
            "confounders": ["age", "income", "severity"],
            "mediator": "adherence"
        }
        
        # Collider DAG: T -> Z <- Y, with confounders
        collider_dag = {
            "name": "collider_bias_dag",
            "description": "DAG with collider bias scenario",
            "variables": {
                "U": {"name": "unmeasured_confounder", "type": "continuous", "description": "Unmeasured confounder"},
                "X": {"name": "measured_confounder", "type": "continuous", "description": "Measured confounder"},
                "T": {"name": "treatment", "type": "binary", "description": "Treatment"},
                "Y": {"name": "outcome", "type": "continuous", "description": "Outcome"},
                "Z": {"name": "collider", "type": "continuous", "description": "Collider variable"}
            },
            "edges": [
                {"from": "U", "to": "T"},
                {"from": "U", "to": "Y"},
                {"from": "X", "to": "T"},
                {"from": "X", "to": "Y"},
                {"from": "T", "to": "Z"},
                {"from": "Y", "to": "Z"}
            ],
            "treatment_variable": "T",
            "outcome_variable": "Y",
            "confounders": ["X"]
        }
        
        return [simple_dag, complex_dag, collider_dag]
    
    def generate_synthetic_data(self, dag: Dict, n_samples: int = 1000) -> Tuple[pd.DataFrame, Dict]:
        """Generate synthetic data based on DAG structure with known ground truth."""
        
        np.random.seed(42)  # For reproducibility
        data = {}
        ground_truth = {"causal_effects": {}, "interventions": {}, "anomalies": {}}
        
        dag_name = dag["name"]
        
        if dag_name == "simple_linear_dag":
            # Generate data for simple linear DAG
            X = np.random.normal(0, 1, n_samples)
            T_logits = 0.5 * X + np.random.normal(0, 0.5, n_samples)
            T = (T_logits > 0).astype(int)
            Y = 2.0 * X + 1.5 * T + np.random.normal(0, 0.5, n_samples)
            
            data = pd.DataFrame({"X": X, "T": T, "Y": Y})
            ground_truth["causal_effects"]["T_on_Y"] = 1.5
            ground_truth["interventions"]["T_1.0_on_Y"] = 1.5
            
            # Calculate distribution shift ground truth (mean difference between halves)
            baseline_mean = data[:n_samples//2]["Y"].mean()
            comparison_mean = data[n_samples//2:]["Y"].mean()
            ground_truth["distribution_shift"] = comparison_mean - baseline_mean
            
            # Counterfactual ground truth (T=1 to T=0 effect)
            ground_truth["counterfactual"] = {"T_1_to_0_effect": -1.5}
            
        elif dag_name == "complex_healthcare_dag":
            # Generate data for complex healthcare DAG
            age = np.random.uniform(18, 80, n_samples)
            income = np.random.exponential(50000, n_samples)
            severity = 0.02 * age + np.random.normal(0, 1, n_samples)
            
            treatment_logits = (
                -2.0 + 0.03 * age + 0.00001 * income + 0.8 * severity + 
                np.random.normal(0, 0.5, n_samples)
            )
            treatment = (treatment_logits > 0).astype(int)
            
            adherence = (
                0.5 + 0.3 * treatment + 0.000005 * income + 
                np.random.normal(0, 0.2, n_samples)
            )
            adherence = np.clip(adherence, 0, 1)
            
            outcome = (
                50 + 0.2 * age - 0.0001 * income - 5 * severity + 
                8 * treatment + 15 * adherence + 
                np.random.normal(0, 2, n_samples)
            )
            
            data = pd.DataFrame({
                "age": age, "income": income, "severity": severity,
                "treatment": treatment, "adherence": adherence, "outcome": outcome
            })
            
            ground_truth["causal_effects"]["treatment_on_outcome"] = 8.0
            ground_truth["interventions"]["treatment_1.0_on_outcome"] = 8.0
            
            # Calculate distribution shift ground truth (mean difference between halves)
            baseline_mean = data[:n_samples//2]["outcome"].mean()
            comparison_mean = data[n_samples//2:]["outcome"].mean()
            ground_truth["distribution_shift"] = comparison_mean - baseline_mean
            
            # Counterfactual ground truth (treatment=1 to treatment=0 effect)
            ground_truth["counterfactual"] = {"treatment_1_to_0_effect": -8.0}
            
        elif dag_name == "collider_bias_dag":
            # Generate data for collider bias DAG
            U = np.random.normal(0, 1, n_samples)
            X = np.random.normal(0, 1, n_samples)
            
            T_logits = 0.5 * U + 0.3 * X + np.random.normal(0, 0.5, n_samples)
            T = (T_logits > 0).astype(int)
            
            Y = 0.7 * U + 0.4 * X + 1.2 * T + np.random.normal(0, 0.5, n_samples)
            Z = 0.6 * T + 0.8 * Y + np.random.normal(0, 0.3, n_samples)
            
            data = pd.DataFrame({"U": U, "X": X, "T": T, "Y": Y, "Z": Z})
            ground_truth["causal_effects"]["T_on_Y"] = 1.2
            ground_truth["interventions"]["T_1.0_on_Y"] = 1.2
            
            # Calculate distribution shift ground truth (mean difference between halves)
            baseline_mean = data[:n_samples//2]["Y"].mean()
            comparison_mean = data[n_samples//2:]["Y"].mean()
            ground_truth["distribution_shift"] = comparison_mean - baseline_mean
            
            # Counterfactual ground truth (T=1 to T=0 effect)
            ground_truth["counterfactual"] = {"T_1_to_0_effect": -1.2}
            
        # Add anomalies for anomaly detection testing
        if len(data) > 100:
            anomaly_indices = np.random.choice(len(data), size=int(0.05 * len(data)), replace=False)
            outcome_var = dag["outcome_variable"]
            original_mean = data[outcome_var].mean()
            data.loc[anomaly_indices, outcome_var] += np.random.normal(3, 1, len(anomaly_indices))
            ground_truth["anomalies"]["count"] = len(anomaly_indices)
            ground_truth["anomalies"]["threshold"] = original_mean + 2 * data[outcome_var].std()
        
        return data, ground_truth
    
    def generate_sample_queries(self, dag: Dict) -> List[Dict]:
        """Generate sample queries for all query types based on DAG."""
        
        queries = []
        
        # Effect Estimation Query
        queries.append({
            "query_type": "effect_estimation",
            "treatment_variable": dag["treatment_variable"],
            "outcome_variable": dag["outcome_variable"],
            "confounders": dag.get("confounders", []),
            "treatment_value": 1.0
        })
        
        # Anomaly Attribution Query
        outcome_var = dag["outcome_variable"]
        potential_causes = [v for v in dag["variables"].keys() if v != outcome_var]
        queries.append({
            "query_type": "anomaly_attribution",
            "outcome_variable": outcome_var,
            "anomaly_threshold": 10.0,  # Will be adjusted based on data
            "potential_causes": potential_causes[:3]  # Limit to avoid complexity
        })
        
        # Distribution Shift Attribution Query
        queries.append({
            "query_type": "distribution_shift_attribution",
            "target_variable": outcome_var,
            "baseline_period": "baseline",
            "comparison_period": "comparison",
            "potential_drivers": dag.get("confounders", [])[:2]
        })
        
        # Intervention Query
        queries.append({
            "query_type": "intervention",
            "intervention_variable": dag["treatment_variable"],
            "intervention_value": 1.0,
            "outcome_variables": [outcome_var]
        })
        
        # Counterfactual Query
        if dag["treatment_variable"] in ["T", "treatment"]:
            factual_scenario = {dag["treatment_variable"]: 1}
            counterfactual_scenario = {dag["treatment_variable"]: 0}
            
            # Add confounder values
            if dag.get("confounders"):
                conf_var = dag["confounders"][0]
                factual_scenario[conf_var] = 0.5
                counterfactual_scenario[conf_var] = 0.5
            
            queries.append({
                "query_type": "counterfactual",
                "factual_scenario": factual_scenario,
                "counterfactual_scenario": counterfactual_scenario,
                "outcome_variable": outcome_var,
                "evidence_variables": dag.get("confounders", [])[:1]
            })
        
        return queries
    
    def run_test_case(self, dag: Dict, query: Dict, data: pd.DataFrame, 
                     ground_truth: Dict) -> Dict:
        """Run a single test case and return results."""
        
        test_result = {
            "dag_name": dag["name"],
            "query_type": query["query_type"],
            "status": "PASS",
            "error": None,
            "estimated_value": None,
            "ground_truth_value": None,
            "absolute_error": None,
            "relative_error": None,
            "execution_time": None
        }
        
        # Save temporary files
        dag_file = self.output_dir / f"temp_dag_{dag['name']}.json"
        data_file = self.output_dir / f"temp_data_{dag['name']}.csv"
        
        try:
            # Save DAG and data
            with open(dag_file, 'w') as f:
                json.dump(dag, f, indent=2)
            data.to_csv(data_file, index=False)
            
            # Adjust anomaly threshold based on actual data
            if query["query_type"] == "anomaly_attribution":
                outcome_var = query["outcome_variable"]
                threshold = data[outcome_var].mean() + 2 * data[outcome_var].std()
                query["anomaly_threshold"] = threshold
            
            # Run the query
            import time
            start_time = time.time()
            result = dispatch_query(query, str(dag_file), str(data_file))
            execution_time = time.time() - start_time
            
            test_result["execution_time"] = execution_time
            
            if not result.get("success", False):
                test_result["status"] = "FAIL"
                test_result["error"] = result.get("error", "Unknown error")
                return test_result
            
            # Extract relevant values for comparison
            if query["query_type"] == "effect_estimation":
                test_result["estimated_value"] = result.get("estimate")
                gt_key = f"{query['treatment_variable']}_on_{query['outcome_variable']}"
                test_result["ground_truth_value"] = ground_truth["causal_effects"].get(gt_key)
                
            elif query["query_type"] == "intervention":
                effects = result.get("intervention_effects", {})
                outcome_var = query["outcome_variables"][0]
                if outcome_var in effects:
                    test_result["estimated_value"] = effects[outcome_var].get("effect")
                    gt_key = f"{query['intervention_variable']}_{query['intervention_value']}_on_{outcome_var}"
                    test_result["ground_truth_value"] = ground_truth["interventions"].get(gt_key)
                    
            elif query["query_type"] == "anomaly_attribution":
                test_result["estimated_value"] = result.get("anomalies_found")
                test_result["ground_truth_value"] = ground_truth["anomalies"].get("count")
                
            elif query["query_type"] == "counterfactual":
                test_result["estimated_value"] = result.get("counterfactual_effect")
                # Extract ground truth from counterfactual scenarios
                treatment_var = query["factual_scenario"].get(dag["treatment_variable"])
                if treatment_var == 1:
                    gt_key = f"{dag['treatment_variable']}_1_to_0_effect"
                else:
                    gt_key = f"{dag['treatment_variable']}_0_to_1_effect"
                test_result["ground_truth_value"] = ground_truth.get("counterfactual", {}).get(gt_key)
                
            elif query["query_type"] == "distribution_shift_attribution":
                test_result["estimated_value"] = result.get("shift_magnitude")
                test_result["ground_truth_value"] = ground_truth.get("distribution_shift")
            
            # Calculate errors if both values are available
            if (test_result["estimated_value"] is not None and 
                test_result["ground_truth_value"] is not None and
                test_result["ground_truth_value"] != "N/A"):
                
                est_val = float(test_result["estimated_value"])
                gt_val = float(test_result["ground_truth_value"])
                
                test_result["absolute_error"] = abs(est_val - gt_val)
                if gt_val != 0:
                    test_result["relative_error"] = abs(est_val - gt_val) / abs(gt_val)
                
                # Define pass/fail criteria
                if query["query_type"] in ["effect_estimation", "intervention"]:
                    if test_result["relative_error"] > 0.5:  # 50% relative error threshold
                        test_result["status"] = "FAIL"
                elif query["query_type"] == "anomaly_attribution":
                    if test_result["absolute_error"] > 10:  # 10 anomalies difference threshold
                        test_result["status"] = "FAIL"
                        
        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            test_result["traceback"] = traceback.format_exc()
            
        finally:
            # Clean up temporary files
            try:
                if dag_file.exists():
                    dag_file.unlink()
                if data_file.exists():
                    data_file.unlink()
            except:
                pass
        
        return test_result
    
    def run_all_tests(self) -> List[Dict]:
        """Run all test cases and return results."""
        
        print("🚀 Starting Comprehensive Causal Analysis Test Bench")
        print("=" * 60)
        
        dags = self.generate_sample_dags()
        all_results = []
        
        for i, dag in enumerate(dags, 1):
            print(f"\n📊 Testing DAG {i}/{len(dags)}: {dag['name']}")
            print("-" * 40)
            
            # Generate synthetic data
            print("  🔧 Generating synthetic data...")
            data, ground_truth = self.generate_synthetic_data(dag)
            print(f"     Generated {len(data)} samples")
            
            # Generate queries
            print("  📝 Generating sample queries...")
            queries = self.generate_sample_queries(dag)
            print(f"     Generated {len(queries)} queries")
            
            # Run each query
            for j, query in enumerate(queries, 1):
                print(f"  ⚡ Running query {j}/{len(queries)}: {query['query_type']}")
                
                result = self.run_test_case(dag, query, data, ground_truth)
                result["test_id"] = f"{dag['name']}_{query['query_type']}"
                all_results.append(result)
                
                status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                print(f"     {status_emoji} {result['status']}")
                
                if result["error"]:
                    print(f"     Error: {result['error']}")
        
        self.results = all_results
        return all_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report in tabular format."""
        
        if not self.results:
            return "No test results available. Run tests first."
        
        # Summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["status"] == "PASS")
        failed_tests = sum(1 for r in self.results if r["status"] == "FAIL")
        error_tests = sum(1 for r in self.results if r["status"] == "ERROR")
        
        report = []
        report.append("🧪 CAUSAL ANALYSIS TEST BENCH REPORT")
        report.append("=" * 50)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        report.append(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        report.append(f"Errors: {error_tests} ({error_tests/total_tests*100:.1f}%)")
        report.append("")
        
        # Detailed results table
        table_data = []
        headers = ["Test ID", "Query Type", "Status", "Est. Value", "GT Value", "Abs Error", "Rel Error", "Time (s)"]
        
        for result in self.results:
            row = [
                result["test_id"],
                result["query_type"],
                result["status"],
                f"{result['estimated_value']:.4f}" if result["estimated_value"] is not None else "N/A",
                f"{result['ground_truth_value']:.4f}" if result["ground_truth_value"] not in [None, "N/A"] else "N/A",
                f"{result['absolute_error']:.4f}" if result["absolute_error"] is not None else "N/A",
                f"{result['relative_error']:.2%}" if result["relative_error"] is not None else "N/A",
                f"{result['execution_time']:.3f}" if result["execution_time"] is not None else "N/A"
            ]
            table_data.append(row)
        
        report.append("📋 DETAILED RESULTS")
        report.append("-" * 30)
        report.append(tabulate(table_data, headers=headers, tablefmt="grid"))
        report.append("")
        
        # Query type performance
        report.append("📊 PERFORMANCE BY QUERY TYPE")
        report.append("-" * 35)
        
        query_types = set(r["query_type"] for r in self.results)
        perf_data = []
        
        for qt in query_types:
            qt_results = [r for r in self.results if r["query_type"] == qt]
            qt_passed = sum(1 for r in qt_results if r["status"] == "PASS")
            qt_total = len(qt_results)
            avg_time = np.mean([r["execution_time"] for r in qt_results if r["execution_time"] is not None])
            
            perf_data.append([
                qt,
                f"{qt_passed}/{qt_total}",
                f"{qt_passed/qt_total*100:.1f}%",
                f"{avg_time:.3f}s"
            ])
        
        perf_headers = ["Query Type", "Pass Rate", "Success %", "Avg Time"]
        report.append(tabulate(perf_data, headers=perf_headers, tablefmt="grid"))
        report.append("")
        
        # Error details
        error_results = [r for r in self.results if r["status"] in ["FAIL", "ERROR"]]
        if error_results:
            report.append("❌ ERROR DETAILS")
            report.append("-" * 20)
            for result in error_results:
                report.append(f"• {result['test_id']}: {result['error']}")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main function to run the test bench."""
    
    # Create and run test bench
    test_bench = CausalTestBench()
    
    try:
        # Generate timestamp for this run
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Run all tests
        results = test_bench.run_all_tests()
        
        # Add metadata to results
        test_metadata = {
            "timestamp": timestamp.isoformat(),
            "test_run_id": timestamp_str,
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r["status"] == "PASS"),
            "failed_tests": sum(1 for r in results if r["status"] == "FAIL"),
            "error_tests": sum(1 for r in results if r["status"] == "ERROR"),
            "test_results": results
        }
        
        # Generate and display report
        report = test_bench.generate_report()
        print("\n" + report)
        
        # Save current report to standard files (overwrites previous)
        report_file = test_bench.output_dir / "test_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        results_file = test_bench.output_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save timestamped versions for historical analysis
        timestamped_report_file = test_bench.output_dir / f"test_report_{timestamp_str}.txt"
        with open(timestamped_report_file, 'w') as f:
            f.write(f"Test Run: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(report)
        
        timestamped_results_file = test_bench.output_dir / f"test_results_{timestamp_str}.json"
        with open(timestamped_results_file, 'w') as f:
            json.dump(test_metadata, f, indent=2, default=str)
        
        # Update historical results log
        history_file = test_bench.output_dir / "test_history.jsonl"
        summary_data = {
            "timestamp": timestamp.isoformat(),
            "test_run_id": timestamp_str,
            "total_tests": test_metadata["total_tests"],
            "passed_tests": test_metadata["passed_tests"],
            "failed_tests": test_metadata["failed_tests"],
            "error_tests": test_metadata["error_tests"],
            "pass_rate": test_metadata["passed_tests"] / test_metadata["total_tests"] if test_metadata["total_tests"] > 0 else 0,
            "avg_execution_time": np.mean([r["execution_time"] for r in results if r["execution_time"] is not None])
        }
        
        with open(history_file, 'a') as f:
            f.write(json.dumps(summary_data, default=str) + "\n")
        
        print(f"\n📄 Current report saved to: {report_file}")
        print(f"📊 Current results saved to: {results_file}")
        print(f"🕐 Timestamped report saved to: {timestamped_report_file}")
        print(f"🕐 Timestamped results saved to: {timestamped_results_file}")
        print(f"📈 Historical summary appended to: {history_file}")
        
    except Exception as e:
        print(f"❌ Test bench failed with error: {e}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())