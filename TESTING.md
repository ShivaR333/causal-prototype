# Causal Analysis Testing Guide

## Overview

This project includes a comprehensive test bench that validates the entire causal analysis system across multiple query types and DAG structures.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Simple Test

```bash
python simple_test.py
```

This runs a minimal test to verify the system is working correctly.

### 3. Run Full Test Bench

```bash
python test_bench.py
```

Or use the convenient wrapper:

```bash
python run_tests.py
```

## Test Results Summary

Based on the latest test run:

### Overall Performance
- **Total Tests**: 15 (5 query types × 3 DAG structures)
- **Success Rate**: 66.7% (10/15 tests passed)
- **Average Execution Time**: ~0.05 seconds per query

### Query Type Performance

| Query Type | Success Rate | Performance Notes |
|------------|-------------|-------------------|
| **Effect Estimation** | 33.3% (1/3) | Works well for simple DAGs, struggles with complex confounding |
| **Intervention** | 100% (3/3) | Excellent performance across all DAG types |
| **Counterfactual** | 100% (3/3) | Reliable counterfactual reasoning |
| **Distribution Shift** | 100% (3/3) | Robust distribution change detection |
| **Anomaly Attribution** | 0% (0/3) | Needs improvement in ground truth generation |

### DAG Structure Performance

1. **Simple Linear DAG** (X → T → Y):
   - Effect estimation: ✅ PASS (1.492 vs 1.500 ground truth)
   - Most query types work well
   
2. **Complex Healthcare DAG**:
   - More challenging due to multiple confounders and mediators
   - Effect estimation shows larger errors due to complexity
   
3. **Collider Bias DAG**:
   - Tests system's ability to handle selection bias
   - Shows expected biases in causal effect estimation

## Test Components

### 1. Sample DAG Generation

The test bench generates three types of DAGs:

- **Simple Linear**: Basic confounded treatment-outcome relationship
- **Complex Healthcare**: Multi-variable healthcare intervention scenario
- **Collider Bias**: Tests handling of selection bias scenarios

### 2. Synthetic Data Generation

- Creates data with **known ground truth** causal effects
- Adds controlled **anomalies** for detection testing
- Uses **reproducible random seeds** for consistent testing

### 3. Query Generation

Automatically generates realistic queries for each DAG:

- Effect estimation with appropriate confounders
- Anomaly detection with realistic thresholds
- Distribution shift analysis
- Intervention scenarios
- Counterfactual comparisons

### 4. Validation and Reporting

- **Ground Truth Comparison**: Compares estimates against known true values
- **Error Metrics**: Absolute and relative error calculations
- **Performance Timing**: Execution time measurement
- **Tabular Reports**: Easy-to-read success/failure summaries

## Known Issues and Solutions

### 1. DoWhy/NetworkX Compatibility

**Issue**: DoWhy 0.8 has compatibility issues with NetworkX 3.x

**Solution**: 
- Downgraded to NetworkX 2.8.x
- Added fallback model creation in `causal_model.py`

### 2. Effect Estimation Accuracy

**Issue**: Some effect estimates show high relative error (>50%)

**Potential Causes**:
- Complex confounding structures
- Limited sample sizes in some scenarios
- DoWhy estimation method limitations

**Improvements**:
- Use larger sample sizes
- Try additional estimation methods
- Improve confounder specification

### 3. Anomaly Attribution Ground Truth

**Issue**: Anomaly attribution tests consistently fail

**Root Cause**: Ground truth generation for anomalies needs refinement

**Next Steps**:
- Improve synthetic anomaly generation
- Better attribution scoring methodology
- More realistic anomaly scenarios

## Test Output Files

After running tests, check these files:

- `test_results/test_report.txt` - Human-readable summary
- `test_results/test_results.json` - Detailed results for analysis
- Individual DAG and data files (cleaned up automatically)

## Interpreting Results

### Success Criteria

- **Effect Estimation**: <50% relative error vs ground truth
- **Anomaly Attribution**: <10 anomalies difference from ground truth
- **Other Queries**: Successful execution without errors

### Warning Signs

- Execution times >1 second may indicate performance issues
- Consistent failures across DAG types suggest systemic problems
- Large error rates may indicate estimation method issues

## Adding New Tests

To add new test scenarios:

1. **New DAG Structures**: Add to `generate_sample_dags()` in `test_bench.py`
2. **New Query Types**: Extend `generate_sample_queries()` method
3. **Custom Validation**: Modify `run_test_case()` for specific validation logic

## Continuous Integration

The test bench is designed for CI/CD integration:

```bash
# Exit code 0 for success, 1 for failure
python run_tests.py
echo $?  # Check exit code
```

Consider setting success thresholds:
- Overall success rate >80% for production
- No errors allowed in critical query types
- Performance regression detection

## Future Improvements

1. **Expand Test Coverage**:
   - More DAG types (instrumental variables, time series)
   - Edge cases (missing data, measurement error)
   - Larger scale datasets

2. **Better Ground Truth**:
   - Analytical solutions where possible
   - Simulation-based validation
   - Cross-validation with other tools

3. **Performance Benchmarking**:
   - Scalability testing
   - Memory usage monitoring
   - Comparison with other causal inference tools

4. **Integration Testing**:
   - API endpoint testing
   - CLI functionality validation
   - Error handling verification