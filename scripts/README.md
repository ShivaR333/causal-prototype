# Test Automation Scripts

This directory contains automated testing scripts for the Causal Analysis Agent system.

## 📋 Scripts Overview

### 🚀 Main Test Suite
**`automated-test-suite.sh`** - Comprehensive automated testing
- Executes 80+ test cases from the test checklist
- Generates detailed Markdown and JSON reports
- Covers all system components and functionality
- Provides pass/fail status and recommendations

**Usage:**
```bash
# Run complete test suite
./scripts/automated-test-suite.sh

# Show help options
./scripts/automated-test-suite.sh --help

# Quick test mode (future enhancement)
./scripts/automated-test-suite.sh --quick

# Skip cleanup
./scripts/automated-test-suite.sh --no-cleanup
```

### ⚡ Quick Health Check
**`quick-health-check.sh`** - Fast system validation
- Validates critical services in under 30 seconds
- Checks service availability and basic functionality
- Perfect for rapid status verification

**Usage:**
```bash
./scripts/quick-health-check.sh
```

### 🔧 Advanced Testing
**`test-runner-helper.js`** - WebSocket and frontend testing
- Requires Node.js for WebSocket connection tests
- Tests authentication flows and real-time communication
- Performance and concurrent connection testing

**Usage:**
```bash
# Install dependencies first
npm install ws

# Run advanced tests
node scripts/test-runner-helper.js
```

### 📊 Report Generation
**`generate-test-report.py`** - HTML report generator
- Converts JSON test results to comprehensive HTML reports
- Visual charts and categorized results
- Professional-grade reporting for stakeholders

**Usage:**
```bash
# Generate HTML report from JSON results
python3 scripts/generate-test-report.py -i test-reports/test_results_TIMESTAMP.json

# Specify output file
python3 scripts/generate-test-report.py -i results.json -o my_report.html
```

## 🔄 Testing Workflow

### 1. Quick Validation
```bash
# Fast health check (30 seconds)
./scripts/quick-health-check.sh
```

### 2. Comprehensive Testing
```bash
# Full test suite (5-10 minutes)
./scripts/automated-test-suite.sh
```

### 3. Advanced Testing (Optional)
```bash
# WebSocket and performance tests
node scripts/test-runner-helper.js
```

### 4. Report Generation
```bash
# Generate visual HTML report
python3 scripts/generate-test-report.py -i test-reports/test_results_*.json
```

## 📁 Generated Reports

All reports are saved to the `test-reports/` directory:

- **`test_report_TIMESTAMP.md`** - Detailed Markdown report
- **`test_results_TIMESTAMP.json`** - Machine-readable JSON results
- **`test_report_TIMESTAMP.html`** - Visual HTML report (via Python script)
- **`advanced_test_results_TIMESTAMP.json`** - Advanced test results

## 🎯 Test Categories

The automated tests cover:

1. **Pre-Test Setup** (Docker, services, resources)
2. **Service Health** (LocalStack, WebSocket, Frontend, etc.)
3. **AWS Resources** (S3, DynamoDB, Lambda, Cognito, Step Functions)
4. **Frontend UI** (Loading, forms, JavaScript)
5. **WebSocket Communication** (Connection, authentication, messaging)
6. **Lambda Functions** (Deployment, invocation, individual functions)
7. **Step Functions** (Workflow execution, state transitions)
8. **Database Operations** (DynamoDB CRUD operations)
9. **S3 Operations** (File upload/download, bucket access)
10. **Performance** (Response times, resource usage)
11. **Security** (Input validation, authentication)
12. **Error Handling** (Failure scenarios, recovery)
13. **Integration** (End-to-end workflows, component communication)

## 🔧 Prerequisites

### Required
- Docker and Docker Compose
- Bash shell
- curl and basic Unix utilities

### Optional (for enhanced testing)
- **Node.js** - For WebSocket connection testing
- **Python 3** - For HTML report generation
- **jq** - For JSON processing (recommended)

### Installing Optional Dependencies

**Node.js WebSocket testing:**
```bash
npm install ws
```

**Python report generation:**
```bash
# No additional packages required (uses built-in libraries)
python3 --version  # Verify Python 3 is available
```

## 🐛 Troubleshooting

### Common Issues

**Permission denied:**
```bash
chmod +x scripts/*.sh
```

**Docker not running:**
```bash
docker info
# Start Docker Desktop if needed
```

**Services not started:**
```bash
docker-compose -f docker-compose.local-cloud.yml up -d
./scripts/automated-test-suite.sh
```

**Node.js WebSocket tests fail:**
```bash
npm install ws
node --version  # Ensure Node.js is installed
```

### Debugging Test Failures

1. **Check service logs:**
   ```bash
   docker-compose -f docker-compose.local-cloud.yml logs [service-name]
   ```

2. **Verify service health:**
   ```bash
   ./scripts/quick-health-check.sh
   ```

3. **Run individual test components:**
   ```bash
   # Test specific AWS resource
   docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal s3 ls
   
   # Test WebSocket manually
   curl -sf http://localhost:8080/health
   ```

4. **Review generated reports:**
   - Check `test-reports/` directory for detailed logs
   - Look for specific failure reasons in JSON reports

## 📈 Continuous Integration

### GitHub Actions Integration
```yaml
name: Automated Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose -f docker-compose.local-cloud.yml up -d
      - name: Run tests
        run: ./scripts/automated-test-suite.sh
      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: test-reports/
```

### Jenkins Integration
```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'docker-compose -f docker-compose.local-cloud.yml up -d'
            }
        }
        stage('Test') {
            steps {
                sh './scripts/automated-test-suite.sh'
            }
        }
        stage('Report') {
            steps {
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'test-reports',
                    reportFiles: '*.html',
                    reportName: 'Test Report'
                ])
            }
        }
    }
}
```

## 🔮 Future Enhancements

- **Load testing** with Artillery.js integration
- **Visual regression testing** with screenshot comparison
- **API contract testing** with OpenAPI validation
- **Security scanning** with OWASP ZAP integration
- **Performance benchmarking** with automated thresholds
- **Cross-browser testing** with Selenium

## 📞 Support

For issues with the testing scripts:

1. Check the troubleshooting section above
2. Review the generated test reports for specific failures
3. Verify all prerequisites are installed
4. Ensure services are running with `quick-health-check.sh`

The automated testing suite is designed to be comprehensive yet maintainable, providing confidence in system reliability while enabling rapid development iteration.