#!/usr/bin/env node

/**
 * Simple test client for the MCP server
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';

async function testMCPServer() {
  console.log('🧪 Testing Geo-Compliance MCP Server...\n');
  
  try {
    // Start the MCP server
    const serverProcess = spawn('node', ['index.js'], {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    // Create client transport
    const transport = new StdioClientTransport({
      spawn: () => serverProcess
    });
    
    const client = new Client(
      {
        name: 'test-client',
        version: '1.0.0',
      },
      {
        capabilities: {},
      }
    );
    
    await client.connect(transport);
    
    // Test 1: List available tools
    console.log('1️⃣ Testing tool listing...');
    const tools = await client.request(
      { method: 'tools/list' },
      {}
    );
    console.log(`✅ Found ${tools.tools?.length || 0} tools`);
    tools.tools?.forEach(tool => {
      console.log(`   - ${tool.name}: ${tool.description}`);
    });
    console.log();
    
    // Test 2: System status
    console.log('2️⃣ Testing system status...');
    const statusResult = await client.request(
      { method: 'tools/call' },
      {
        name: 'get_system_status',
        arguments: {}
      }
    );
    console.log('✅ System status retrieved');
    const statusData = JSON.parse(statusResult.content[0].text);
    console.log(`   Health: ${statusData.status || 'unknown'}`);
    console.log();
    
    // Test 3: Document retrieval
    console.log('3️⃣ Testing document retrieval...');
    const retrieveResult = await client.request(
      { method: 'tools/call' },
      {
        name: 'retrieve_docs',
        arguments: {
          query: 'data protection privacy GDPR',
          top_k: 3
        }
      }
    );
    console.log('✅ Document retrieval test completed');
    const retrieveData = JSON.parse(retrieveResult.content[0].text);
    console.log(`   Retrieved: ${retrieveData.retrieved_count || 0} documents`);
    console.log();
    
    // Test 4: LLM call
    console.log('4️⃣ Testing primary LLM...');
    const llmResult = await client.request(
      { method: 'tools/call' },
      {
        name: 'primary_llm',
        arguments: {
          prompt: 'What are the key principles of GDPR compliance?',
          context: 'This is a test of the MCP server LLM integration.'
        }
      }
    );
    console.log('✅ LLM call test completed');
    const llmData = JSON.parse(llmResult.content[0].text);
    console.log(`   Model used: ${llmData.model_used || 'unknown'}`);
    console.log();
    
    // Test 5: Compliance check
    console.log('5️⃣ Testing compliance analysis...');
    const complianceResult = await client.request(
      { method: 'tools/call' },
      {
        name: 'check_compliance',
        arguments: {
          feature_data: {
            name: 'User Analytics Dashboard',
            description: 'Collects user behavior data for analytics',
            data_types: ['behavioral_data', 'preferences', 'usage_patterns'],
            storage_duration: '2 years',
            third_party_sharing: true
          },
          jurisdiction: 'EU'
        }
      }
    );
    console.log('✅ Compliance analysis test completed');
    const complianceData = JSON.parse(complianceResult.content[0].text);
    console.log(`   Verdict: ${complianceData.verdict || 'unknown'}`);
    console.log(`   Confidence: ${complianceData.confidence || 0}`);
    console.log();
    
    await client.close();
    serverProcess.kill();
    
    console.log('🎉 All tests completed successfully!');
    console.log('\n📋 MCP Server is ready for integration with:');
    console.log('   • VS Code with MCP extension');
    console.log('   • Claude Desktop');
    console.log('   • Custom clients');
    console.log('   • Human-in-the-loop workflows');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run tests
testMCPServer();
