#!/usr/bin/env node

/**
 * Example MCP Client for Geo-Compliance System
 * Demonstrates how to integrate with the MCP server
 */

import { spawn } from 'child_process';

class ComplianceMCPClient {
  constructor() {
    this.serverProcess = null;
  }

  async startServer() {
    console.log('🚀 Starting MCP Server...');
    
    this.serverProcess = spawn('node', ['index.js'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: process.cwd()
    });

    // Wait a moment for server to initialize
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    console.log('✅ MCP Server started');
  }

  async callTool(toolName, args = {}) {
    return new Promise((resolve, reject) => {
      const request = {
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args
        }
      };

      let response = '';
      let error = '';

      this.serverProcess.stdout.on('data', (data) => {
        response += data.toString();
      });

      this.serverProcess.stderr.on('data', (data) => {
        error += data.toString();
      });

      // Send request
      this.serverProcess.stdin.write(JSON.stringify(request) + '\n');

      // Wait for response (simplified - in real implementation you'd parse JSONRPC properly)
      setTimeout(() => {
        if (error) {
          reject(new Error(error));
        } else {
          try {
            // Parse last line as response (simplified)
            const lines = response.trim().split('\n');
            const lastLine = lines[lines.length - 1];
            const result = JSON.parse(lastLine);
            resolve(result);
          } catch (e) {
            resolve({ content: [{ type: 'text', text: response }] });
          }
        }
      }, 2000);
    });
  }

  async analyzeFeature(featureData, jurisdiction = 'EU') {
    console.log(`🔍 Analyzing feature for ${jurisdiction} compliance...`);
    
    try {
      const result = await this.callTool('check_compliance', {
        feature_data: featureData,
        jurisdiction: jurisdiction
      });

      console.log('📊 Analysis completed:');
      
      if (result.content && result.content[0]) {
        const analysis = JSON.parse(result.content[0].text);
        
        console.log(`   Verdict: ${analysis.verdict}`);
        console.log(`   Confidence: ${(analysis.confidence * 100).toFixed(1)}%`);
        console.log(`   Risk Level: ${analysis.risk_level}`);
        
        if (analysis.human_review_triggered) {
          console.log('⚠️  Human review has been triggered');
        }
        
        return analysis;
      }
    } catch (error) {
      console.error('❌ Analysis failed:', error.message);
      throw error;
    }
  }

  async getSystemHealth() {
    console.log('🏥 Checking system health...');
    
    try {
      const result = await this.callTool('get_system_status');
      
      if (result.content && result.content[0]) {
        const status = JSON.parse(result.content[0].text);
        
        console.log(`   Overall Status: ${status.status}`);
        console.log(`   Health: ${status.health_percentage}%`);
        
        return status;
      }
    } catch (error) {
      console.error('❌ Health check failed:', error.message);
      throw error;
    }
  }

  async searchDocuments(query, topK = 5) {
    console.log(`🔎 Searching for: "${query}"...`);
    
    try {
      const result = await this.callTool('retrieve_docs', {
        query: query,
        top_k: topK
      });

      if (result.content && result.content[0]) {
        const searchResult = JSON.parse(result.content[0].text);
        
        console.log(`   Found: ${searchResult.retrieved_count} documents`);
        
        return searchResult;
      }
    } catch (error) {
      console.error('❌ Document search failed:', error.message);
      throw error;
    }
  }

  async stop() {
    if (this.serverProcess) {
      this.serverProcess.kill();
      console.log('🛑 MCP Server stopped');
    }
  }
}

// Example usage
async function example() {
  const client = new ComplianceMCPClient();
  
  try {
    await client.startServer();
    
    // Example 1: System health check
    await client.getSystemHealth();
    console.log();
    
    // Example 2: Document search
    await client.searchDocuments('GDPR data protection');
    console.log();
    
    // Example 3: Compliance analysis
    const testFeature = {
      name: 'User Analytics Dashboard',
      description: 'Tracks user behavior and preferences',
      data_types: ['behavioral_data', 'preferences', 'location_data'],
      storage_duration: '2 years',
      third_party_sharing: true,
      user_consent: 'implied',
      data_retention_policy: 'automatic_deletion'
    };
    
    const analysis = await client.analyzeFeature(testFeature, 'EU');
    
    console.log('\n🎯 Example Integration Complete!');
    console.log('This demonstrates how to:');
    console.log('• Check system health');
    console.log('• Search regulatory documents');
    console.log('• Analyze features for compliance');
    console.log('• Handle human-in-the-loop workflows');
    
  } catch (error) {
    console.error('💥 Example failed:', error);
  } finally {
    await client.stop();
  }
}

// Run example if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  example();
}

export { ComplianceMCPClient };
