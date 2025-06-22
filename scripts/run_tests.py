#!/usr/bin/env python3
"""
Simple script to run the causal analysis test bench.

Usage:
    python run_tests.py
"""

from test_bench import CausalTestBench

if __name__ == "__main__":
    print("🧪 Running Causal Analysis Test Bench")
    print("=" * 50)
    
    # Create test bench
    test_bench = CausalTestBench(output_dir="test_results")
    
    # Run all tests
    results = test_bench.run_all_tests()
    
    # Generate report
    report = test_bench.generate_report()
    print("\n" + report)
    
    # Calculate overall success rate
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["status"] == "PASS")
    success_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
    
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 Test bench PASSED - System is working well!")
    elif success_rate >= 60:
        print("⚠️  Test bench PARTIAL - Some issues detected")
    else:
        print("❌ Test bench FAILED - Significant issues detected")