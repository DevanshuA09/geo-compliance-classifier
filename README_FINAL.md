# 🌍 README_FINAL: Complete Guide to Geo-Compliance Classifier MCP Server

This comprehensive guide explains how to run the Model Context Protocol (MCP) server, query using LLMs, and use all the tools and architecture components of the Geo-Compliance Classifier system.

## 📋 Table of Contents

1. [System Architecture Overview](#-system-architecture-overview)
2. [MCP Server Setup](#-mcp-server-setup)
3. [LLM Integration](#-llm-integration)
4. [Tool Registry & Available Tools](#-tool-registry--available-tools)
5. [Usage Examples](#-usage-examples)
6. [API Endpoints](#-api-endpoints)
7. [Configuration Management](#-configuration-management)
8. [Troubleshooting](#-troubleshooting)
9. [Advanced Usage Patterns](#-advanced-usage-patterns)

## 🏗️ System Architecture Overview

The Geo-Compliance Classifier uses a Model Context Protocol (MCP) architecture that orchestrates multiple AI components for automated compliance analysis:

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLM Interface Layer                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │   Chat Client   │ │   API Client    │ │   Python SDK    │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST API
┌─────────────────────────▼───────────────────────────────────────┐
│                    MCP Server Bridge                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                MCP Orchestrator                             │ │
│  │  • Request routing                                          │ │
│  │  • Tool execution                                           │ │
│  │  • Response formatting                                      │ │
│  │  • Performance monitoring                                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     Tool Registry                               │
│  ┌───────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │ Compliance Tools  │ │  Retrieval      │ │   Evidence      │ │
│  │ • Feature Gen     │ │  • RAG System   │ │   • Logging     │ │
│  │ • Risk Analysis   │ │  • Vector Index │ │   • Export      │ │
│  │ • Validation      │ │  • Semantic     │ │   • Audit       │ │
│  └───────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  Data Processing Layer                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │ Artifact        │ │ Legal Text      │ │ Feature Data    │  │
│  │ Preprocessor    │ │ Processing      │ │ Generation      │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

- **MCP Orchestrator**: Central coordinator that manages LLM interactions and tool execution
- **Tool Registry**: Dynamic registry of available compliance analysis tools
- **RAG System**: Retrieval-Augmented Generation for regulation context
- **Vector Index**: FAISS-based semantic search over legal texts
- **Compliance Analyzers**: Specialized tools for different regulatory frameworks
- **Evidence System**: Audit logging and compliance evidence collection

## 🚀 MCP Server Setup

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure all required components are available
pip install transformers torch sentence-transformers faiss-cpu uvicorn fastapi
```

### 1. Start the MCP Server

```bash
# Method 1: Using the start script
python start_mcp_service.py

# Method 2: Direct uvicorn command
uvicorn retriever.service:app --host 0.0.0.0 --port 8000 --reload

# Method 3: With custom configuration
python start_mcp_service.py --config config/custom_config.yaml --port 8080
```

**Expected Output:**
```
🚀 Starting MCP Server Bridge...
Service will be available at: http://localhost:8000
MCP endpoints:
  - POST /mcp/analyze
  - GET  /mcp/tools
  - GET  /mcp/status
  - GET  /docs (OpenAPI documentation)

Press Ctrl+C to stop the service
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     MCP orchestrator initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Verify Server Status

```bash
# Test server health
curl http://localhost:8000/health

# Check MCP status
curl http://localhost:8000/mcp/status

# List available tools
curl http://localhost:8000/mcp/tools
```

## 🤖 LLM Integration

### Local LLM Setup

The system supports multiple LLM providers and can run models locally or through APIs.

#### Configuration in `config.yaml`:

```yaml
mcp:
  enabled: true
  model:
    provider: "transformers_local"  # or "hf_inference" for API
    name: "mistral-7b-instruct"     # model name
    device: "cuda"                  # or "cpu"
    max_length: 2048
    temperature: 0.7
    endpoint_url: null              # for API providers
  
  # Tool execution settings
  tools:
    timeout: 30
    max_parallel: 3
    error_handling: "graceful"
```

#### Supported LLM Providers:

1. **Local Transformers (Recommended)**
```python
# Automatic model loading
config = {
    "provider": "transformers_local",
    "name": "microsoft/DialoGPT-medium",  # or any HF model
    "device": "cuda"  # or "cpu"
}
```

2. **Hugging Face Inference API**
```python
config = {
    "provider": "hf_inference",
    "name": "mistralai/Mistral-7B-Instruct-v0.1",
    "endpoint_url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
    "api_token": "your_hf_token"
}
```

3. **OpenAI Compatible APIs**
```python
config = {
    "provider": "openai_compatible",
    "endpoint_url": "http://localhost:1234/v1",
    "model": "local-model",
    "api_key": "not-needed"
}
```

### LLM Query Examples

#### Basic Compliance Query

```python
import requests

# Query the MCP server
response = requests.post("http://localhost:8000/mcp/analyze", json={
    "user_query": "Analyze this feature for GDPR compliance: Age verification system that collects biometric data from EU users",
    "tools_required": ["compliance_analyzer", "regulation_retriever"],
    "context": {
        "jurisdiction": "EU",
        "regulation": "GDPR",
        "feature_type": "age_verification"
    }
})

result = response.json()
print(f"Compliance Status: {result['compliance']['status']}")
print(f"Confidence: {result['compliance']['confidence']}")
print(f"Violations: {result['compliance']['violations']}")
```

#### Feature Generation with Context

```python
response = requests.post("http://localhost:8000/mcp/analyze", json={
    "user_query": "Generate 5 social media features that would be compliant with California SB976",
    "tools_required": ["compliance_analyzer"],
    "context": {
        "jurisdiction": "US-CA",
        "regulation": "SB976",
        "count": 5,
        "target_age": "13-17"
    }
})

features = response.json()['analysis_results']
for feature in features:
    print(f"Feature: {feature['title']}")
    print(f"Compliance: {feature['label']}")
    print(f"Rationale: {feature['rationale']}")
    print("---")
```

## 🛠️ Tool Registry & Available Tools

The MCP server provides a dynamic registry of compliance analysis tools. Each tool has specific capabilities and use cases.

### Available Tools

#### 1. **Compliance Analyzer** (`compliance_analyzer`)

**Purpose**: Analyzes features against specific regulatory requirements

**Parameters**:
```json
{
  "feature_description": "string",
  "jurisdiction": "string (EU|US-CA|US-FL|etc.)",
  "regulation": "string (DSA|GDPR|SB976|etc.)",
  "age_range": "string (optional)",
  "data_types": ["array of strings"]
}
```

**Example Usage**:
```python
tool_request = {
    "tool": "compliance_analyzer",
    "parameters": {
        "feature_description": "Infinite scroll feed with personalized content recommendations based on user behavior patterns",
        "jurisdiction": "EU",
        "regulation": "DSA",
        "age_range": "all",
        "data_types": ["behavior_patterns", "engagement_metrics"]
    }
}

response = requests.post("http://localhost:8000/mcp/tools/execute", json=tool_request)
```

**Response Format**:
```json
{
  "compliance_status": "non_compliant",
  "confidence": 0.87,
  "violations": [
    {
      "regulation": "DSA Article 38",
      "description": "Recommender systems lack transparency options",
      "severity": "high",
      "recommendation": "Implement user controls for algorithmic transparency"
    }
  ],
  "required_mitigations": ["user_controls", "transparency_reporting"],
  "evidence": [...],
  "risk_score": 8.5
}
```

#### 2. **Compliance Analyzer** (`compliance_analyzer`)

**Purpose**: Analyzes features for regulatory compliance across jurisdictions

**Parameters**:
```json
{
  "feature_data": "object",
  "regulation": "string",
  "jurisdiction": "string",
  "analysis_type": "string (compliance|risk|recommendations|etc.)",
  "compliance_requirements": ["array"]
}
```

**Example Usage**:
```python
tool_request = {
    "tool": "compliance_analyzer",
    "parameters": {
        "feature_data": {"name": "age_verification", "type": "safety"},
        "regulation": "HB3",
        "jurisdiction": "US-FL",
        "analysis_type": "compliance",
        "compliance_requirements": ["parental_controls", "content_filtering"]
    }
}

response = requests.post("http://localhost:8000/mcp/tools/execute", json=tool_request)
```

#### 3. **Regulation Retriever** (`regulation_retriever`)

**Purpose**: Semantic search across legal texts and regulations

**Parameters**:
```json
{
  "query": "string",
  "jurisdiction": "string (optional)",
  "regulation": "string (optional)",
  "top_k": "integer",
  "include_context": "boolean"
}
```

**Example Usage**:
```python
tool_request = {
    "tool": "regulation_retriever",
    "parameters": {
        "query": "age verification requirements for social media platforms",
        "jurisdiction": "US-CA",
        "top_k": 5,
        "include_context": true
    }
}
```

#### 4. **Evidence Exporter** (`evidence_exporter`)

**Purpose**: Generates compliance evidence and audit documentation

**Parameters**:
```json
{
  "analysis_id": "string",
  "export_format": "string (json|pdf|html)",
  "include_regulatory_context": "boolean",
  "include_decision_trail": "boolean"
}
```

#### 5. **Risk Assessor** (`risk_assessor`)

**Purpose**: Evaluates compliance risk scores and mitigation strategies

**Parameters**:
```json
{
  "feature_data": "object",
  "jurisdiction": "string",
  "assessment_type": "string (comprehensive|quick|targeted)",
  "risk_tolerance": "string (low|medium|high)"
}
```

### Tool Discovery

```python
# Get all available tools
response = requests.get("http://localhost:8000/mcp/tools")
tools = response.json()['tools']

for tool in tools:
    print(f"Tool: {tool['name']}")
    print(f"Description: {tool['description']}")
    print(f"Parameters: {tool['parameters']}")
    print("---")
```

## 🎯 Usage Examples

### Example 1: Complete Feature Compliance Analysis

```python
import requests
import json

# Step 1: Analyze feature compliance
analysis_response = requests.post("http://localhost:8000/mcp/analyze", json={
    "user_query": """
    Analyze this TikTok feature for EU DSA compliance:
    
    Feature: Smart Content Feed
    Description: AI-powered content recommendation system that analyzes user interactions, 
    viewing time, and engagement patterns to deliver personalized content. The system 
    tracks user behavior across sessions and uses machine learning to optimize engagement.
    
    Target users: EU users aged 13+
    Data collected: viewing history, interaction patterns, device info, approximate location
    """,
    "tools_required": ["compliance_analyzer", "regulation_retriever", "risk_assessor"],
    "context": {
        "jurisdiction": "EU",
        "regulation": "DSA",
        "feature_type": "recommendation_system"
    }
})

analysis = analysis_response.json()

# Step 2: Generate evidence report
evidence_response = requests.post("http://localhost:8000/mcp/tools/execute", json={
    "tool": "evidence_exporter",
    "parameters": {
        "analysis_id": analysis['analysis_id'],
        "export_format": "json",
        "include_regulatory_context": True,
        "include_decision_trail": True
    }
})

evidence = evidence_response.json()

# Step 3: Display results
print("=== COMPLIANCE ANALYSIS RESULTS ===")
print(f"Status: {analysis['compliance']['status']}")
print(f"Confidence: {analysis['compliance']['confidence']}")
print(f"Risk Score: {analysis['risk']['score']}")

print("\n=== VIOLATIONS FOUND ===")
for violation in analysis['compliance']['violations']:
    print(f"• {violation['regulation']}: {violation['description']}")

print("\n=== REQUIRED MITIGATIONS ===")
for mitigation in analysis['compliance']['required_mitigations']:
    print(f"• {mitigation}")

print("\n=== EVIDENCE PACKAGE ===")
print(f"Evidence ID: {evidence['evidence_id']}")
print(f"Regulatory References: {len(evidence['regulatory_context'])} documents")
print(f"Decision Trail: {len(evidence['decision_trail'])} steps")
```

### Example 2: Multi-Jurisdiction Feature Generation

```python
# Analyze features for compliance across multiple jurisdictions
jurisdictions = ["EU", "US-CA", "US-FL"]
all_compliance_reports = []

for jurisdiction in jurisdictions:
    response = requests.post("http://localhost:8000/mcp/analyze", json={
        "user_query": f"Analyze advertising features for compliance with {jurisdiction} regulations for social media platforms",
        "tools_required": ["compliance_analyzer"],
        "context": {
            "jurisdiction": jurisdiction,
            "feature_domain": "advertising",
            "analysis_type": "compliance",
            "target_age": "all"
        }
    })
    
    report = response.json()['analysis_results']
    all_compliance_reports.extend(report)

# Find universally compliant features
universal_features = []
for feature in all_features:
    if feature['label'] == 'compliant':
        universal_features.append(feature)

print(f"Found {len(universal_features)} universally compliant features:")
for feature in universal_features:
    print(f"• {feature['title']} ({feature['geo_country']})")
```

### Example 3: Real-time Compliance Monitoring

```python
import time
import threading

class ComplianceMonitor:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.monitoring = False
        
    def monitor_features(self, features_file):
        """Monitor features for compliance changes."""
        self.monitoring = True
        
        while self.monitoring:
            # Read features from file
            with open(features_file, 'r') as f:
                features = json.load(f)
            
            for feature in features:
                # Analyze each feature
                response = requests.post(f"{self.server_url}/mcp/analyze", json={
                    "user_query": f"Check compliance status for: {feature['description']}",
                    "tools_required": ["compliance_analyzer"],
                    "context": {
                        "jurisdiction": feature.get('jurisdiction', 'EU'),
                        "feature_id": feature['id']
                    }
                })
                
                result = response.json()
                
                # Check for compliance violations
                if result['compliance']['status'] == 'non_compliant':
                    self.alert_violation(feature['id'], result)
            
            time.sleep(300)  # Check every 5 minutes
    
    def alert_violation(self, feature_id, analysis):
        print(f"🚨 COMPLIANCE VIOLATION DETECTED!")
        print(f"Feature ID: {feature_id}")
        print(f"Violations: {len(analysis['compliance']['violations'])}")
        for violation in analysis['compliance']['violations']:
            print(f"  • {violation['regulation']}: {violation['description']}")

# Usage
monitor = ComplianceMonitor()
monitor.monitor_features("features_to_monitor.json")
```

## 🌐 API Endpoints

### Health & Status Endpoints

```bash
# Check server health
GET /health
Response: {"status": "healthy", "total_chunks": 1250, "uptime": 3600}

# MCP status
GET /mcp/status
Response: {
  "status": "ready",
  "llm_status": "loaded",
  "tools_available": 8,
  "total_requests": 45,
  "average_latency": 2.3
}
```

### Tool Management

```bash
# List all available tools
GET /mcp/tools
Response: {
  "tools": [
    {
      "name": "compliance_analyzer",
      "description": "Analyzes features against regulatory requirements",
      "parameters": {...},
      "capabilities": ["analysis", "risk_assessment"]
    }
  ]
}

# Execute specific tool
POST /mcp/tools/execute
Body: {
  "tool": "compliance_analyzer",
  "parameters": {...}
}
```

### Analysis Endpoints

```bash
# Main analysis endpoint
POST /mcp/analyze
Body: {
  "user_query": "string",
  "tools_required": ["array"],
  "context": {...}
}

# Batch analysis
POST /mcp/analyze/batch
Body: {
  "queries": [...],
  "common_context": {...}
}
```

### Retrieval Endpoints

```bash
# Search regulations
GET /search?query=age%20verification&jurisdiction=US-CA&top_k=5

# Get regulation context
GET /regulation/{regulation_id}/context

# Semantic search
POST /search/semantic
Body: {
  "query": "content moderation requirements",
  "filters": {"jurisdiction": "EU"}
}
```

## ⚙️ Configuration Management

### Main Configuration File (`config.yaml`)

```yaml
# Core system configuration
system:
  name: "geo-compliance-classifier"
  version: "1.0.0"
  debug: false

# Model configuration
embedding:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  max_length: 384
  device: "cuda"  # or "cpu"
  batch_size: 32

# MCP Server configuration
mcp:
  enabled: true
  model:
    provider: "transformers_local"
    name: "mistral-7b-instruct"
    device: "cuda"
    max_length: 2048
    temperature: 0.7
    load_in_8bit: false
  
  tools:
    timeout: 30
    max_parallel: 3
    error_handling: "graceful"
    
  performance:
    cache_size: 1000
    batch_processing: true
    async_execution: true

# RAG system configuration
rag:
  vectorstore:
    type: "faiss"
    index_path: "index/faiss/index.faiss"
    metric: "cosine"
    normalize: true
  
  retriever:
    top_k: 5
    score_threshold: 0.7
    diversity_penalty: 0.1
  
  reranker:
    enabled: true
    model: "cross-encoder/ms-marco-MiniLM-L-2-v2"

# Jurisdiction-specific settings
jurisdictions:
  EU:
    regulations: ["DSA", "GDPR", "DMA"]
    age_thresholds: {"minor": 16, "child": 13}
    risk_tolerance: "low"
  
  "US-CA":
    regulations: ["SB976", "COPPA"]
    age_thresholds: {"minor": 18, "child": 13}
    risk_tolerance: "medium"
  
  "US-FL":
    regulations: ["HB3", "COPPA"]
    age_thresholds: {"minor": 18, "child": 13}
    risk_tolerance: "medium"

# Performance monitoring
monitoring:
  enabled: true
  metrics:
    - "request_latency"
    - "tool_execution_time"
    - "compliance_accuracy"
    - "error_rate"
  
  alerts:
    latency_threshold: 5.0
    error_threshold: 0.05
    compliance_confidence_threshold: 0.8
```

### Environment Variables

```bash
# Set environment variables for production
export COMPLIANCE_CONFIG_PATH="/path/to/config.yaml"
export HF_TOKEN="your_hugging_face_token"
export CUDA_VISIBLE_DEVICES="0,1"
export LOG_LEVEL="INFO"
export MCP_PORT="8000"
export MCP_HOST="0.0.0.0"

# For development
export DEBUG="true"
export LOG_LEVEL="DEBUG"
export MCP_MODEL_CACHE="/tmp/model_cache"
```

### Dynamic Configuration Updates

```python
# Update configuration at runtime
response = requests.post("http://localhost:8000/mcp/config/update", json={
    "mcp.model.temperature": 0.5,
    "rag.retriever.top_k": 10,
    "jurisdictions.EU.risk_tolerance": "high"
})

# Get current configuration
response = requests.get("http://localhost:8000/mcp/config")
config = response.json()
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Server Won't Start

**Problem**: ImportError or module not found
```bash
ModuleNotFoundError: No module named 'transformers'
```

**Solution**:
```bash
# Install missing dependencies
pip install -r requirements.txt

# For development
pip install -r requirements_dev.txt

# Verify installation
python -c "import transformers; print('OK')"
```

#### 2. Model Loading Failures

**Problem**: CUDA out of memory or model loading timeout
```bash
RuntimeError: CUDA out of memory
```

**Solution**:
```yaml
# Update config.yaml
mcp:
  model:
    device: "cpu"  # Use CPU instead
    load_in_8bit: true  # Reduce memory usage
    max_length: 1024  # Reduce context length
```

#### 3. Tool Execution Timeouts

**Problem**: Tools taking too long to execute
```bash
TimeoutError: Tool execution exceeded 30 seconds
```

**Solution**:
```yaml
# Increase timeout in config.yaml
mcp:
  tools:
    timeout: 60  # Increase to 60 seconds
    max_parallel: 1  # Reduce parallel execution
```

#### 4. Index Not Found

**Problem**: Vector index missing or corrupted
```bash
FileNotFoundError: Index file not found at index/faiss/index.faiss
```

**Solution**:
```bash
# Rebuild the index
python -m index.build_index --legal-texts ./legal_texts --output ./index

# Or use the simplified version
python -m index.build_simple_index
```

#### 5. Configuration Validation Errors

**Problem**: Invalid configuration format
```bash
yaml.YAMLError: Invalid YAML syntax
```

**Solution**:
```bash
# Validate configuration
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Reset to default
cp config/centralized_rag_config.yaml config.yaml
```

### Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start server with debug logging
python start_mcp_service.py --debug

# Check logs
tail -f logs/mcp_server.log
```

### Performance Monitoring

```python
# Get server performance metrics
response = requests.get("http://localhost:8000/mcp/metrics")
metrics = response.json()

print(f"Total Requests: {metrics['total_requests']}")
print(f"Average Latency: {metrics['average_latency']:.2f}s")
print(f"Error Rate: {metrics['error_rate']:.2%}")
print(f"Tool Success Rate: {metrics['tool_success_rate']:.2%}")

# Get detailed performance breakdown
response = requests.get("http://localhost:8000/mcp/metrics/detailed")
detailed = response.json()

for tool_name, stats in detailed['tools'].items():
    print(f"{tool_name}: {stats['avg_time']:.2f}s avg, {stats['success_rate']:.2%} success")
```

## 🚀 Advanced Usage Patterns

### 1. Custom Tool Development

Create your own compliance analysis tools:

```python
from src.mcp.tool_registry import ToolDefinition

def custom_gdpr_analyzer(feature_data, parameters):
    """Custom GDPR compliance analyzer."""
    # Your custom analysis logic
    return {
        "gdpr_compliant": True,
        "data_minimization_score": 0.8,
        "consent_requirements": ["explicit", "specific"],
        "retention_recommendations": "12 months max"
    }

# Register the tool
tool_def = ToolDefinition(
    name="custom_gdpr_analyzer",
    description="Custom GDPR compliance analysis",
    function=custom_gdpr_analyzer,
    parameters={
        "feature_data": {"type": "object", "required": True},
        "analysis_depth": {"type": "string", "default": "standard"}
    }
)

# Add to registry
registry = ToolRegistry()
registry.register_tool(tool_def)
```

### 2. Batch Processing Pipeline

Process multiple features efficiently:

```python
import asyncio
import aiohttp

async def batch_analyze_features(features, jurisdiction="EU"):
    """Analyze multiple features concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for feature in features:
            task = analyze_feature_async(session, feature, jurisdiction)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results

async def analyze_feature_async(session, feature, jurisdiction):
    """Asynchronously analyze a single feature."""
    async with session.post(
        "http://localhost:8000/mcp/analyze",
        json={
            "user_query": f"Analyze for {jurisdiction} compliance: {feature['description']}",
            "tools_required": ["compliance_analyzer"],
            "context": {"jurisdiction": jurisdiction}
        }
    ) as response:
        return await response.json()

# Usage
features = [
    {"id": "f1", "description": "Age verification system..."},
    {"id": "f2", "description": "Content recommendation engine..."},
    {"id": "f3", "description": "Parental control dashboard..."}
]

results = asyncio.run(batch_analyze_features(features, "EU"))
```

### 3. Real-time Compliance Streaming

Monitor compliance in real-time:

```python
import websockets
import json

async def compliance_stream():
    """Stream real-time compliance updates."""
    uri = "ws://localhost:8000/mcp/stream"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to compliance events
        await websocket.send(json.dumps({
            "action": "subscribe",
            "events": ["compliance_violation", "risk_change", "regulation_update"]
        }))
        
        # Listen for events
        async for message in websocket:
            event = json.loads(message)
            
            if event['type'] == 'compliance_violation':
                print(f"🚨 Violation: {event['feature_id']} - {event['regulation']}")
            elif event['type'] == 'risk_change':
                print(f"⚠️ Risk Update: {event['feature_id']} - Risk: {event['new_risk']}")
            elif event['type'] == 'regulation_update':
                print(f"📋 Regulation Update: {event['regulation']} - {event['change']}")

# Run the streaming client
asyncio.run(compliance_stream())
```

### 4. Integration with External Systems

Connect to external compliance systems:

```python
class ExternalComplianceIntegration:
    def __init__(self, mcp_url="http://localhost:8000"):
        self.mcp_url = mcp_url
        
    def sync_with_legal_system(self, legal_system_api):
        """Sync with external legal compliance system."""
        # Get features from external system
        external_features = legal_system_api.get_features()
        
        compliance_results = []
        
        for feature in external_features:
            # Analyze with MCP
            result = self.analyze_feature(feature)
            
            # Update external system
            legal_system_api.update_compliance_status(
                feature['id'], 
                result['compliance']['status']
            )
            
            compliance_results.append(result)
        
        return compliance_results
    
    def analyze_feature(self, feature):
        """Analyze single feature via MCP."""
        response = requests.post(f"{self.mcp_url}/mcp/analyze", json={
            "user_query": f"Analyze compliance: {feature['description']}",
            "tools_required": ["compliance_analyzer", "risk_assessor"],
            "context": {
                "jurisdiction": feature.get('jurisdiction', 'EU'),
                "external_id": feature['id']
            }
        })
        return response.json()

# Usage with external legal system
integration = ExternalComplianceIntegration()
results = integration.sync_with_legal_system(external_legal_api)
```

## 📊 Example Complete Workflow

Here's a complete workflow that demonstrates the full capabilities of the system:

```python
import requests
import json
import time

class ComplianceWorkflow:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        
    def complete_compliance_analysis(self, feature_description, jurisdiction="EU"):
        """Complete end-to-end compliance analysis workflow."""
        
        print("🚀 Starting Complete Compliance Analysis")
        print("=" * 50)
        
        # Step 1: Initial compliance analysis
        print("Step 1: Analyzing feature compliance...")
        analysis_result = self.analyze_compliance(feature_description, jurisdiction)
        
        # Step 2: Risk assessment
        print("Step 2: Performing risk assessment...")
        risk_result = self.assess_risk(feature_description, jurisdiction)
        
        # Step 3: Regulation retrieval
        print("Step 3: Retrieving relevant regulations...")
        regulations = self.retrieve_regulations(feature_description, jurisdiction)
        
        # Step 4: Generate evidence package
        print("Step 4: Generating evidence package...")
        evidence = self.generate_evidence(analysis_result, risk_result, regulations)
        
        # Step 5: Create compliance report
        print("Step 5: Creating compliance report...")
        report = self.create_compliance_report(
            feature_description, 
            analysis_result, 
            risk_result, 
            regulations, 
            evidence
        )
        
        print("✅ Analysis Complete!")
        return report
    
    def analyze_compliance(self, feature_description, jurisdiction):
        """Analyze feature compliance."""
        response = requests.post(f"{self.server_url}/mcp/analyze", json={
            "user_query": f"Analyze this feature for {jurisdiction} compliance: {feature_description}",
            "tools_required": ["compliance_analyzer"],
            "context": {"jurisdiction": jurisdiction}
        })
        return response.json()
    
    def assess_risk(self, feature_description, jurisdiction):
        """Assess compliance risk."""
        response = requests.post(f"{self.server_url}/mcp/tools/execute", json={
            "tool": "risk_assessor",
            "parameters": {
                "feature_description": feature_description,
                "jurisdiction": jurisdiction,
                "assessment_type": "comprehensive"
            }
        })
        return response.json()
    
    def retrieve_regulations(self, feature_description, jurisdiction):
        """Retrieve relevant regulations."""
        response = requests.post(f"{self.server_url}/mcp/tools/execute", json={
            "tool": "regulation_retriever",
            "parameters": {
                "query": f"regulations for: {feature_description}",
                "jurisdiction": jurisdiction,
                "top_k": 5,
                "include_context": True
            }
        })
        return response.json()
    
    def generate_evidence(self, analysis, risk, regulations):
        """Generate compliance evidence."""
        response = requests.post(f"{self.server_url}/mcp/tools/execute", json={
            "tool": "evidence_exporter",
            "parameters": {
                "analysis_data": analysis,
                "risk_data": risk,
                "regulatory_context": regulations,
                "export_format": "json"
            }
        })
        return response.json()
    
    def create_compliance_report(self, feature_desc, analysis, risk, regulations, evidence):
        """Create final compliance report."""
        return {
            "feature_description": feature_desc,
            "analysis_timestamp": time.time(),
            "compliance_status": analysis.get('compliance', {}).get('status', 'unknown'),
            "confidence_score": analysis.get('compliance', {}).get('confidence', 0),
            "risk_score": risk.get('risk_score', 0),
            "violations": analysis.get('compliance', {}).get('violations', []),
            "mitigations": analysis.get('compliance', {}).get('required_mitigations', []),
            "regulatory_references": len(regulations.get('results', [])),
            "evidence_package_id": evidence.get('evidence_id', None),
            "next_review_date": time.time() + (30 * 24 * 3600),  # 30 days
            "action_items": self.generate_action_items(analysis, risk)
        }
    
    def generate_action_items(self, analysis, risk):
        """Generate actionable items from analysis."""
        items = []
        
        # High risk items
        if risk.get('risk_score', 0) > 7:
            items.append("URGENT: Address high-risk compliance issues immediately")
        
        # Violation-based items
        for violation in analysis.get('compliance', {}).get('violations', []):
            items.append(f"Fix: {violation.get('description', 'Unknown violation')}")
        
        # Mitigation items
        for mitigation in analysis.get('compliance', {}).get('required_mitigations', []):
            items.append(f"Implement: {mitigation}")
        
        return items

# Example usage
workflow = ComplianceWorkflow()

# Analyze a complex feature
feature = """
Smart Content Recommendation Engine:
- Uses AI to analyze user behavior patterns, engagement history, and content preferences
- Collects viewing time, interaction data, and demographic information
- Provides personalized content recommendations to maximize engagement
- Targets users aged 13+ in EU markets
- Stores user data for 24 months for recommendation improvement
- Shares aggregated data with advertising partners
"""

report = workflow.complete_compliance_analysis(feature, "EU")

# Display results
print("\n" + "="*50)
print("FINAL COMPLIANCE REPORT")
print("="*50)
print(f"Compliance Status: {report['compliance_status']}")
print(f"Confidence Score: {report['confidence_score']:.2%}")
print(f"Risk Score: {report['risk_score']}/10")
print(f"Violations Found: {len(report['violations'])}")
print(f"Required Mitigations: {len(report['mitigations'])}")
print(f"Regulatory References: {report['regulatory_references']}")

print("\nAction Items:")
for i, item in enumerate(report['action_items'], 1):
    print(f"{i}. {item}")

print(f"\nEvidence Package ID: {report['evidence_package_id']}")
print(f"Next Review Date: {time.ctime(report['next_review_date'])}")
```

This comprehensive guide provides everything you need to run, configure, and use the Geo-Compliance Classifier MCP server effectively. The system is designed to be both powerful for complex compliance analysis and simple to use for everyday compliance checking tasks.
