#!/usr/bin/env python3
"""
Test History Analyzer for Causal Analysis System

This script analyzes historical test results to identify trends and patterns.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from typing import List, Dict

def load_test_history(history_file: Path) -> pd.DataFrame:
    """Load test history from JSONL file."""
    
    if not history_file.exists():
        print(f"History file not found: {history_file}")
        return pd.DataFrame()
    
    history_data = []
    with open(history_file, 'r') as f:
        for line in f:
            if line.strip():
                history_data.append(json.loads(line))
    
    if not history_data:
        print("No historical data found")
        return pd.DataFrame()
    
    df = pd.DataFrame(history_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.sort_values('timestamp')

def analyze_trends(df: pd.DataFrame) -> Dict:
    """Analyze trends in test performance."""
    
    if df.empty:
        return {}
    
    analysis = {
        "total_runs": len(df),
        "date_range": {
            "start": df['timestamp'].min().isoformat(),
            "end": df['timestamp'].max().isoformat()
        },
        "pass_rate_stats": {
            "mean": df['pass_rate'].mean(),
            "std": df['pass_rate'].std(),
            "min": df['pass_rate'].min(),
            "max": df['pass_rate'].max(),
            "latest": df['pass_rate'].iloc[-1] if len(df) > 0 else None
        },
        "execution_time_stats": {
            "mean": df['avg_execution_time'].mean(),
            "std": df['avg_execution_time'].std(),
            "min": df['avg_execution_time'].min(),
            "max": df['avg_execution_time'].max(),
            "latest": df['avg_execution_time'].iloc[-1] if len(df) > 0 else None
        }
    }
    
    # Calculate trends
    if len(df) > 1:
        # Pass rate trend
        x = np.arange(len(df))
        pass_rate_trend = np.polyfit(x, df['pass_rate'], 1)[0]
        time_trend = np.polyfit(x, df['avg_execution_time'], 1)[0]
        
        analysis["trends"] = {
            "pass_rate_slope": pass_rate_trend,
            "pass_rate_direction": "improving" if pass_rate_trend > 0 else "declining" if pass_rate_trend < 0 else "stable",
            "execution_time_slope": time_trend,
            "execution_time_direction": "increasing" if time_trend > 0 else "decreasing" if time_trend < 0 else "stable"
        }
    
    return analysis

def generate_plots(df: pd.DataFrame, output_dir: Path):
    """Generate plots for test history analysis."""
    
    if df.empty:
        print("No data to plot")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Test Performance History Analysis', fontsize=16)
    
    # Pass rate over time
    ax1.plot(df['timestamp'], df['pass_rate'] * 100, marker='o', linewidth=2, markersize=6)
    ax1.set_title('Pass Rate Over Time')
    ax1.set_ylabel('Pass Rate (%)')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Execution time over time
    ax2.plot(df['timestamp'], df['avg_execution_time'] * 1000, marker='s', color='orange', linewidth=2, markersize=6)
    ax2.set_title('Average Execution Time Over Time')
    ax2.set_ylabel('Execution Time (ms)')
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Pass rate distribution
    ax3.hist(df['pass_rate'] * 100, bins=10, alpha=0.7, color='green', edgecolor='black')
    ax3.set_title('Pass Rate Distribution')
    ax3.set_xlabel('Pass Rate (%)')
    ax3.set_ylabel('Frequency')
    ax3.grid(True, alpha=0.3)
    
    # Test counts over time
    ax4.bar(range(len(df)), df['total_tests'], alpha=0.7, color='purple')
    ax4.set_title('Total Tests per Run')
    ax4.set_xlabel('Test Run')
    ax4.set_ylabel('Number of Tests')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_file = output_dir / "test_history_analysis.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"📈 Plots saved to: {plot_file}")
    plt.close()

def load_detailed_results(results_dir: Path) -> pd.DataFrame:
    """Load detailed results from all timestamped result files."""
    
    detailed_data = []
    
    # Find all timestamped result files
    result_files = list(results_dir.glob("test_results_*.json"))
    
    for file in result_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                
            # Extract test run metadata
            run_metadata = {
                "test_run_id": data["test_run_id"],
                "timestamp": data["timestamp"],
                "total_tests": data["total_tests"],
                "passed_tests": data["passed_tests"],
                "failed_tests": data["failed_tests"]
            }
            
            # Add individual test results
            for test_result in data["test_results"]:
                combined_result = {**run_metadata, **test_result}
                detailed_data.append(combined_result)
                
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not detailed_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(detailed_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.sort_values('timestamp')

def analyze_query_performance(df: pd.DataFrame) -> Dict:
    """Analyze performance by query type across all runs."""
    
    if df.empty:
        return {}
    
    query_analysis = {}
    
    for query_type in df['query_type'].unique():
        query_data = df[df['query_type'] == query_type]
        
        query_analysis[query_type] = {
            "total_runs": len(query_data),
            "pass_rate": (query_data['status'] == 'PASS').mean(),
            "avg_execution_time": query_data['execution_time'].mean(),
            "avg_absolute_error": query_data['absolute_error'].mean() if 'absolute_error' in query_data.columns else None,
            "avg_relative_error": query_data['relative_error'].mean() if 'relative_error' in query_data.columns else None
        }
    
    return query_analysis

def main():
    """Main function to analyze test history."""
    
    results_dir = Path("test_results")
    
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return 1
    
    print("🔍 Analyzing Test History")
    print("=" * 40)
    
    # Load and analyze summary history
    history_file = results_dir / "test_history.jsonl"
    history_df = load_test_history(history_file)
    
    if not history_df.empty:
        print(f"\n📊 Found {len(history_df)} test runs")
        
        # Analyze trends
        trends = analyze_trends(history_df)
        
        print(f"\n📈 Performance Trends:")
        print(f"  • Pass Rate: {trends['pass_rate_stats']['mean']:.1%} ± {trends['pass_rate_stats']['std']:.1%}")
        print(f"  • Latest Pass Rate: {trends['pass_rate_stats']['latest']:.1%}")
        print(f"  • Avg Execution Time: {trends['execution_time_stats']['mean']*1000:.1f}ms ± {trends['execution_time_stats']['std']*1000:.1f}ms")
        
        if "trends" in trends:
            print(f"  • Pass Rate Trend: {trends['trends']['pass_rate_direction']}")
            print(f"  • Execution Time Trend: {trends['trends']['execution_time_direction']}")
        
        # Generate plots
        try:
            generate_plots(history_df, results_dir)
        except ImportError:
            print("⚠️  Matplotlib not available, skipping plot generation")
        except Exception as e:
            print(f"⚠️  Error generating plots: {e}")
    
    # Load and analyze detailed results
    detailed_df = load_detailed_results(results_dir)
    
    if not detailed_df.empty:
        print(f"\n🔬 Detailed Analysis of {len(detailed_df)} individual test results")
        
        query_performance = analyze_query_performance(detailed_df)
        
        print(f"\n📋 Performance by Query Type:")
        for query_type, stats in query_performance.items():
            print(f"  • {query_type}:")
            print(f"    - Pass Rate: {stats['pass_rate']:.1%}")
            print(f"    - Avg Time: {stats['avg_execution_time']*1000:.1f}ms")
            if stats['avg_absolute_error'] is not None:
                print(f"    - Avg Abs Error: {stats['avg_absolute_error']:.4f}")
            if stats['avg_relative_error'] is not None:
                print(f"    - Avg Rel Error: {stats['avg_relative_error']:.1%}")
    
    # Save analysis results
    analysis_file = results_dir / "history_analysis.json"
    analysis_data = {
        "generated_at": datetime.now().isoformat(),
        "summary_trends": trends if not history_df.empty else {},
        "query_performance": query_performance if not detailed_df.empty else {}
    }
    
    with open(analysis_file, 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    
    print(f"\n💾 Analysis saved to: {analysis_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())