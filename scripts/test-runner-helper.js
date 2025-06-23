#!/usr/bin/env node

/**
 * Helper script for advanced WebSocket and frontend testing
 * Requires Node.js to run WebSocket connection tests
 */

const WebSocket = require('ws');
const http = require('http');
const https = require('https');

class TestRunner {
    constructor() {
        this.results = [];
        this.timeout = 10000; // 10 seconds
    }

    async runTest(name, testFunction) {
        console.log(`[INFO] Running: ${name}`);
        
        try {
            const result = await Promise.race([
                testFunction(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Test timeout')), this.timeout)
                )
            ]);
            
            console.log(`[PASS] ${name}`);
            this.results.push({ name, status: 'PASS', result });
            return true;
        } catch (error) {
            console.log(`[FAIL] ${name}: ${error.message}`);
            this.results.push({ name, status: 'FAIL', error: error.message });
            return false;
        }
    }

    // Test WebSocket connection
    async testWebSocketConnection() {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket('ws://localhost:8080');
            
            ws.on('open', () => {
                ws.close();
                resolve('WebSocket connection successful');
            });
            
            ws.on('error', (error) => {
                reject(error);
            });
            
            setTimeout(() => {
                reject(new Error('WebSocket connection timeout'));
            }, 5000);
        });
    }

    // Test WebSocket authentication
    async testWebSocketAuth() {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket('ws://localhost:8080');
            
            ws.on('open', () => {
                // Send auth message
                ws.send(JSON.stringify({
                    action: 'auth',
                    payload: {
                        token: 'test-token',
                        userId: 'test-user'
                    }
                }));
            });
            
            ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data);
                    if (message.action === 'auth_success') {
                        ws.close();
                        resolve('WebSocket authentication successful');
                    } else if (message.action === 'connection') {
                        // Continue waiting for auth response
                    } else {
                        reject(new Error(`Unexpected response: ${message.action}`));
                    }
                } catch (error) {
                    reject(new Error('Invalid JSON response'));
                }
            });
            
            ws.on('error', (error) => {
                reject(error);
            });
            
            setTimeout(() => {
                reject(new Error('WebSocket auth timeout'));
            }, 8000);
        });
    }

    // Test WebSocket query flow
    async testWebSocketQuery() {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket('ws://localhost:8080');
            let authenticated = false;
            
            ws.on('open', () => {
                // First authenticate
                ws.send(JSON.stringify({
                    action: 'auth',
                    payload: {
                        token: 'test-token',
                        userId: 'test-user'
                    }
                }));
            });
            
            ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data);
                    
                    if (message.action === 'auth_success' && !authenticated) {
                        authenticated = true;
                        // Send test query
                        ws.send(JSON.stringify({
                            action: 'query',
                            sessionId: 'test-session',
                            messageId: 'test-message',
                            payload: {
                                type: 'natural_language',
                                content: 'Test query for automation'
                            }
                        }));
                    } else if (message.action === 'query_received') {
                        ws.close();
                        resolve('WebSocket query flow successful');
                    } else if (message.action === 'error') {
                        reject(new Error(`Server error: ${message.error}`));
                    }
                } catch (error) {
                    reject(new Error('Invalid JSON response'));
                }
            });
            
            ws.on('error', (error) => {
                reject(error);
            });
            
            setTimeout(() => {
                reject(new Error('WebSocket query timeout'));
            }, 15000);
        });
    }

    // Test HTTP endpoint
    async testHttpEndpoint(url, expectedContent) {
        return new Promise((resolve, reject) => {
            const client = url.startsWith('https') ? https : http;
            
            client.get(url, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        if (expectedContent && !data.includes(expectedContent)) {
                            reject(new Error(`Expected content "${expectedContent}" not found`));
                        } else {
                            resolve(`HTTP ${res.statusCode} - Content OK`);
                        }
                    } else {
                        reject(new Error(`HTTP ${res.statusCode}`));
                    }
                });
            }).on('error', (error) => {
                reject(error);
            });
        });
    }

    // Test frontend JavaScript loading
    async testFrontendJS() {
        const response = await this.testHttpEndpoint('http://localhost:3000');
        
        // Check if the page includes Next.js scripts
        return new Promise((resolve, reject) => {
            http.get('http://localhost:3000', (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    if (data.includes('_next/static') || data.includes('webpack')) {
                        resolve('Frontend JavaScript bundles detected');
                    } else {
                        reject(new Error('No JavaScript bundles found'));
                    }
                });
            }).on('error', reject);
        });
    }

    // Test API response time
    async testResponseTime(url, maxTime = 2000) {
        const start = Date.now();
        await this.testHttpEndpoint(url);
        const duration = Date.now() - start;
        
        if (duration > maxTime) {
            throw new Error(`Response time ${duration}ms exceeds ${maxTime}ms`);
        }
        
        return `Response time: ${duration}ms`;
    }

    // Test concurrent connections
    async testConcurrentConnections(count = 5) {
        const connections = [];
        
        for (let i = 0; i < count; i++) {
            connections.push(this.testWebSocketConnection());
        }
        
        const results = await Promise.allSettled(connections);
        const successful = results.filter(r => r.status === 'fulfilled').length;
        
        if (successful < count) {
            throw new Error(`Only ${successful}/${count} connections successful`);
        }
        
        return `${successful} concurrent connections successful`;
    }

    // Generate JSON report
    generateReport() {
        const summary = {
            total: this.results.length,
            passed: this.results.filter(r => r.status === 'PASS').length,
            failed: this.results.filter(r => r.status === 'FAIL').length
        };
        
        return {
            timestamp: new Date().toISOString(),
            summary,
            results: this.results
        };
    }

    async runAllTests() {
        console.log('🧪 Starting Advanced Test Suite');
        console.log('================================');
        
        // WebSocket Tests
        await this.runTest(
            'WebSocket Connection',
            () => this.testWebSocketConnection()
        );
        
        await this.runTest(
            'WebSocket Authentication',
            () => this.testWebSocketAuth()
        );
        
        await this.runTest(
            'WebSocket Query Flow',
            () => this.testWebSocketQuery()
        );
        
        // HTTP Tests
        await this.runTest(
            'Frontend Loading',
            () => this.testHttpEndpoint('http://localhost:3000', 'Causal Analysis')
        );
        
        await this.runTest(
            'WebSocket Gateway Health',
            () => this.testHttpEndpoint('http://localhost:8080/health')
        );
        
        await this.runTest(
            'Frontend JavaScript',
            () => this.testFrontendJS()
        );
        
        // Performance Tests
        await this.runTest(
            'Frontend Response Time',
            () => this.testResponseTime('http://localhost:3000', 3000)
        );
        
        await this.runTest(
            'WebSocket Gateway Response Time',
            () => this.testResponseTime('http://localhost:8080/health', 1000)
        );
        
        // Concurrent Connection Test
        await this.runTest(
            'Concurrent WebSocket Connections',
            () => this.testConcurrentConnections(3)
        );
        
        // Generate and save report
        const report = this.generateReport();
        
        console.log('\n📊 Advanced Test Results:');
        console.log(`Total: ${report.summary.total}`);
        console.log(`Passed: ${report.summary.passed} ✅`);
        console.log(`Failed: ${report.summary.failed} ❌`);
        
        // Write results to file
        const fs = require('fs');
        const path = require('path');
        
        const reportDir = path.join(__dirname, '..', 'test-reports');
        if (!fs.existsSync(reportDir)) {
            fs.mkdirSync(reportDir, { recursive: true });
        }
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportFile = path.join(reportDir, `advanced_test_results_${timestamp}.json`);
        
        fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
        console.log(`\n📝 Report saved to: ${reportFile}`);
        
        return report.summary.failed === 0;
    }
}

// Main execution
if (require.main === module) {
    const runner = new TestRunner();
    
    runner.runAllTests().then(success => {
        process.exit(success ? 0 : 1);
    }).catch(error => {
        console.error('Test runner failed:', error);
        process.exit(1);
    });
}

module.exports = TestRunner;