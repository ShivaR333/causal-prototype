#!/usr/bin/env python3

"""
Test Report Generator
Processes test results and generates comprehensive HTML and PDF reports
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

class TestReportGenerator:
    def __init__(self, report_dir):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        
    def load_test_results(self, json_file):
        """Load test results from JSON file"""
        try:
            with open(json_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading test results: {e}")
            return None
    
    def generate_html_report(self, test_data, output_file):
        """Generate comprehensive HTML report"""
        
        summary = test_data.get('test_run', {}).get('summary', {})
        results = test_data.get('test_run', {}).get('results', [])
        timestamp = test_data.get('test_run', {}).get('timestamp', 'unknown')
        
        # Calculate additional metrics
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        pass_rate = summary.get('pass_rate', 0)
        
        # Categorize tests
        categories = self._categorize_tests(results)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Causal Analysis Agent - Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header .subtitle {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        .metric.pass {{ background: #d4edda; }}
        .metric.fail {{ background: #f8d7da; }}
        .metric.skip {{ background: #fff3cd; }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .pass-rate {{
            font-size: 3em;
            color: {self._get_pass_rate_color(pass_rate)};
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            color: #333;
        }}
        .category {{
            margin-bottom: 30px;
        }}
        .category h3 {{
            background: #f8f9fa;
            padding: 15px;
            margin: 0 0 15px 0;
            border-left: 4px solid #007bff;
        }}
        .test-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }}
        .test-item {{
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #ddd;
        }}
        .test-item.pass {{
            background: #d4edda;
            border-color: #c3e6cb;
        }}
        .test-item.fail {{
            background: #f8d7da;
            border-color: #f5c6cb;
        }}
        .test-item.skip {{
            background: #fff3cd;
            border-color: #ffeaa7;
        }}
        .test-name {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .test-status {{
            font-size: 0.9em;
            color: #666;
        }}
        .status-icon {{
            font-size: 1.2em;
            margin-right: 5px;
        }}
        .charts {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 30px 0;
        }}
        .chart {{
            text-align: center;
        }}
        .donut {{
            width: 200px;
            height: 200px;
            margin: 0 auto;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 0 0 8px 8px;
            color: #666;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Report</h1>
            <div class="subtitle">Causal Analysis Agent - Automated Test Suite</div>
            <div class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Run: {timestamp}</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 Summary</h2>
                <div class="summary">
                    <div class="metric">
                        <div class="metric-value">{total}</div>
                        <div class="metric-label">Total Tests</div>
                    </div>
                    <div class="metric pass">
                        <div class="metric-value">{passed}</div>
                        <div class="metric-label">Passed ✅</div>
                    </div>
                    <div class="metric fail">
                        <div class="metric-value">{failed}</div>
                        <div class="metric-label">Failed ❌</div>
                    </div>
                    <div class="metric skip">
                        <div class="metric-value">{skipped}</div>
                        <div class="metric-label">Skipped ⏸️</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value pass-rate">{pass_rate}%</div>
                        <div class="metric-label">Pass Rate</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🎯 Overall Assessment</h2>
                {self._generate_assessment(pass_rate, failed)}
            </div>
            
            <div class="section">
                <h2>📋 Detailed Results</h2>
                {self._generate_category_sections(categories)}
            </div>
            
            <div class="section">
                <h2>📈 Test Distribution</h2>
                <div class="charts">
                    <div class="chart">
                        <h3>Status Distribution</h3>
                        <div class="donut" id="statusChart"></div>
                    </div>
                    <div class="chart">
                        <h3>Category Coverage</h3>
                        <div class="donut" id="categoryChart"></div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔧 Recommendations</h2>
                {self._generate_recommendations(failed, skipped, pass_rate)}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Causal Analysis Agent Test Suite</p>
            <p>For detailed logs and debugging information, check the test-reports directory</p>
        </div>
    </div>
    
    <script>
        // Simple visualization using CSS
        document.addEventListener('DOMContentLoaded', function() {{
            // Status chart data
            const statusData = [
                {{ label: 'Passed', value: {passed}, color: '#28a745' }},
                {{ label: 'Failed', value: {failed}, color: '#dc3545' }},
                {{ label: 'Skipped', value: {skipped}, color: '#ffc107' }}
            ];
            
            createDonutChart('statusChart', statusData);
        }});
        
        function createDonutChart(elementId, data) {{
            const element = document.getElementById(elementId);
            const total = data.reduce((sum, item) => sum + item.value, 0);
            
            let html = '<div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">';
            
            data.forEach((item, index) => {{
                const percentage = (item.value / total) * 100;
                html += `<div style="margin: 5px 0;">
                    <span style="display: inline-block; width: 20px; height: 20px; background: ${{item.color}}; margin-right: 10px;"></span>
                    ${{item.label}}: ${{item.value}} (${{percentage.toFixed(1)}}%)
                </div>`;
            }});
            
            html += '</div>';
            element.innerHTML = html;
        }}
    </script>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_file}")
    
    def _get_pass_rate_color(self, pass_rate):
        if pass_rate >= 95:
            return "#28a745"  # Green
        elif pass_rate >= 80:
            return "#ffc107"  # Yellow
        else:
            return "#dc3545"  # Red
    
    def _categorize_tests(self, results):
        """Categorize tests by type"""
        categories = {
            "Setup & Health": [],
            "Authentication": [],
            "WebSocket": [],
            "Lambda Functions": [],
            "Database": [],
            "Frontend": [],
            "Performance": [],
            "Security": [],
            "Integration": [],
            "Other": []
        }
        
        for result in results:
            name = result.get('name', '')
            category = "Other"
            
            if any(keyword in name.lower() for keyword in ['setup', 'health', 'docker', 'service']):
                category = "Setup & Health"
            elif any(keyword in name.lower() for keyword in ['auth', 'login', 'token', 'cognito']):
                category = "Authentication"
            elif any(keyword in name.lower() for keyword in ['websocket', 'connection', 'gateway']):
                category = "WebSocket"
            elif any(keyword in name.lower() for keyword in ['lambda', 'function']):
                category = "Lambda Functions"
            elif any(keyword in name.lower() for keyword in ['dynamodb', 'database', 'table', 's3']):
                category = "Database"
            elif any(keyword in name.lower() for keyword in ['frontend', 'ui', 'javascript', 'css']):
                category = "Frontend"
            elif any(keyword in name.lower() for keyword in ['performance', 'response time', 'concurrent']):
                category = "Performance"
            elif any(keyword in name.lower() for keyword in ['security', 'xss', 'injection', 'validation']):
                category = "Security"
            elif any(keyword in name.lower() for keyword in ['integration', 'end-to-end']):
                category = "Integration"
            
            categories[category].append(result)
        
        return categories
    
    def _generate_category_sections(self, categories):
        """Generate HTML for test categories"""
        html = ""
        
        for category, tests in categories.items():
            if not tests:
                continue
            
            html += f'<div class="category"><h3>{category} ({len(tests)} tests)</h3><div class="test-grid">'
            
            for test in tests:
                status = test.get('status', 'UNKNOWN').lower()
                name = test.get('name', 'Unknown Test')
                
                icon = "✅" if status == "pass" else "❌" if status == "fail" else "⏸️"
                
                html += f'''
                <div class="test-item {status}">
                    <div class="test-name">
                        <span class="status-icon">{icon}</span>
                        {name}
                    </div>
                    <div class="test-status">{status.upper()}</div>
                </div>
                '''
            
            html += '</div></div>'
        
        return html
    
    def _generate_assessment(self, pass_rate, failed):
        """Generate overall assessment"""
        if failed == 0 and pass_rate >= 95:
            return '''
            <div style="padding: 20px; background: #d4edda; border-radius: 8px; border-left: 5px solid #28a745;">
                <h3 style="color: #155724; margin-top: 0;">✅ SYSTEM READY FOR PRODUCTION</h3>
                <p>All critical tests passed successfully. The system is ready for deployment.</p>
            </div>
            '''
        elif failed <= 2 and pass_rate >= 85:
            return '''
            <div style="padding: 20px; background: #fff3cd; border-radius: 8px; border-left: 5px solid #ffc107;">
                <h3 style="color: #856404; margin-top: 0;">⚠️ READY WITH MINOR ISSUES</h3>
                <p>Minor issues identified but system is functional. Review failed tests before deployment.</p>
            </div>
            '''
        else:
            return '''
            <div style="padding: 20px; background: #f8d7da; border-radius: 8px; border-left: 5px solid #dc3545;">
                <h3 style="color: #721c24; margin-top: 0;">❌ NOT READY FOR PRODUCTION</h3>
                <p>Critical issues found. System requires fixes before deployment.</p>
            </div>
            '''
    
    def _generate_recommendations(self, failed, skipped, pass_rate):
        """Generate recommendations based on test results"""
        recommendations = []
        
        if failed > 0:
            recommendations.append(f"🔧 <strong>Fix {failed} failed test(s)</strong> before deployment")
            recommendations.append("🔄 Re-run the test suite after implementing fixes")
        
        if skipped > 0:
            recommendations.append(f"📝 Consider implementing {skipped} skipped test(s) for complete coverage")
        
        if pass_rate < 90:
            recommendations.append("📈 Investigate and improve test reliability")
        
        recommendations.extend([
            "📊 Set up continuous monitoring for production environment",
            "🤖 Integrate this test suite into CI/CD pipeline",
            "📋 Create runbooks for handling failed scenarios",
            "🔍 Review and update test cases regularly"
        ])
        
        html = "<ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"
        
        return html

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive test reports')
    parser.add_argument('--input', '-i', required=True, help='Input JSON test results file')
    parser.add_argument('--output', '-o', help='Output HTML file (optional)')
    parser.add_argument('--report-dir', '-d', default='test-reports', help='Report directory')
    
    args = parser.parse_args()
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(args.report_dir, f'test_report_{timestamp}.html')
    
    # Generate report
    generator = TestReportGenerator(args.report_dir)
    test_data = generator.load_test_results(args.input)
    
    if test_data:
        generator.generate_html_report(test_data, output_file)
        print(f"✅ Test report generated successfully: {output_file}")
    else:
        print("❌ Failed to generate report")
        sys.exit(1)

if __name__ == '__main__':
    main()