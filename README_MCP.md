# MCP Server Bridge Implementation

## Overview

The MCP (Model Context Protocol) Server Bridge provides a unified interface for compliance analysis using Hugging Face LLMs and orchestrated tool execution. This implementation extends the existing compliance system with intelligent decision-making capabilities.

## Architecture

### Core Components

1. **MCPOrchestrator** (`src/mcp/orchestrator.py`)
   - Main orchestrator class that loads Hugging Face LLMs
   - Manages tool execution workflow
   - Makes final compliance decisions using LLM reasoning

2. **ToolRegistry** (`src/mcp/tool_registry.py`)
   - Manages 9 compliance analysis tools
   - Provides timeout and retry logic
   - Tracks tool usage and performance

3. **FastAPI Endpoints** (`retriever/service.py`)
   - `/mcp/analyze` - Main analysis endpoint
   - `/mcp/tools` - Tool registry information
   - `/mcp/status` - Service health and status

4. **Dashboard Integration** (`Compliance Dashboard/src/components/MCPChat.tsx`)
   - Chat interface for feature analysis
   - Real-time tool usage visualization
   - Decision confidence and reasoning display

## Tool Categories

The system implements 9 core compliance analysis tools:

1. **retrieve_rag** - FAISS vector search and RAG retrieval
2. **analyze_compliance** - Feature compliance analysis
3. **report_compliance** - Compliance reporting and recommendations
4. **map_lookup** - Jurisdiction and policy mapping
5. **evidence_log** - Evidence logging and tracking
6. **export_csv** - CSV export functionality
7. **index_status** - FAISS index health monitoring
8. **glossary_lookup** - Regulatory terminology lookup
9. **feature_generate** - Synthetic feature generation

## Configuration

### MCP Configuration (config.yaml)

```yaml
mcp:
  enabled: true
  model:
    provider: "transformers_local"  # transformers_local | hf_inference
    name: "mistral-7b-instruct"    # Default model
    endpoint_url: null              # For HF inference
    temperature: 0.1
    max_tokens: 2048
  max_tool_steps: 5
  tool_timeout_s: 30
  total_timeout_s: 120
  enable_deterministic: false
```

### Model Providers

- **transformers_local**: Uses local Hugging Face models (default)
- **hf_inference**: Uses Hugging Face Inference Endpoints
- **fallback**: Graceful degradation when LLM unavailable

## API Endpoints

### POST /mcp/analyze

Main analysis endpoint for compliance decisions.

**Request Schema:**
```json
{
  "request_id": "optional-uuid",
  "feature_id": "unique-feature-identifier",
  "feature_title": "Feature Name",
  "description": "Feature description",
  "artifacts": ["PRD", "TRD"],
  "region_hint": "EU|US-CA|US-FL|Global",
  "dataset_tag": "optional-tag"
}
```

**Response Schema:**
```json
{
  "request_id": "uuid",
  "decision_flag": true,
  "confidence": 0.85,
  "reasoning_text": "Detailed reasoning",
  "related_regulations": ["EUDSA", "FL_HB3"],
  "tools_used": [...],
  "retrieval_metadata": {...},
  "model_metadata": {...},
  "timings_ms": {...},
  "evidence_record_path": "path/to/evidence.jsonl"
}
```

### GET /mcp/tools

Returns registered tools with schemas and descriptions.

### GET /mcp/status

Returns service health, LLM status, and performance metrics.

## Usage Examples

### Python Client

```python
import requests

# Analyze a feature
response = requests.post("http://localhost:8000/mcp/analyze", json={
    "feature_id": "age_verification_eu",
    "feature_title": "Age Verification for EU Users",
    "description": "Requires parental consent for users under 16",
    "region_hint": "EU"
})

result = response.json()
print(f"Decision: {result['decision_flag']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Reasoning: {result['reasoning_text']}")
```

### Dashboard Chat

1. Open the Compliance Dashboard at `http://localhost:3000`
2. Navigate to the "MCP Compliance Analysis" section
3. Enter feature description in the chat interface
4. View real-time analysis results and tool usage

## Testing

### Run Test Suite

```bash
# Start the FastAPI service
cd /path/to/project
python -m retriever.service

# In another terminal, run tests
python test_mcp.py
```

### Test Scenarios

The test suite validates:

1. **Service Health** - Basic service availability
2. **MCP Endpoints** - All three MCP endpoints functional
3. **Feature Analysis** - Three representative test cases:
   - EU age verification (positive legal logic flag)
   - Global except Korea (ambiguous case)
   - Indonesia age gating (positive legal logic flag)
4. **Evidence Logging** - MCP decisions properly logged
5. **CSV Export** - Challenge CSV format generation

## Performance

### Latency Targets

- **P50**: < 2 seconds
- **P95**: < 5 seconds
- **Tool Timeout**: 30 seconds per tool
- **Total Timeout**: 120 seconds per analysis

### Optimization Features

- Tool execution caching
- Parallel tool execution where possible
- Graceful degradation on failures
- Performance monitoring and metrics

## Security & Quality

### Security Features

- PII redaction before evidence logging
- Rate limiting on analysis endpoints
- Input validation and sanitization
- Secure configuration management

### Quality Assurance

- Comprehensive error handling
- Fallback mechanisms for all components
- Evidence audit trail
- Performance monitoring

## Troubleshooting

### Common Issues

1. **LLM Not Loading**
   - Check model name and provider in config
   - Verify transformers/torch installation
   - Check available GPU memory

2. **FAISS Index Issues**
   - Verify index files exist in `index/faiss/`
   - Check index build process
   - Validate embedding model compatibility

3. **Tool Execution Failures**
   - Check tool timeouts in config
   - Verify tool dependencies
   - Review error logs for specific failures

### Debug Mode

Enable debug logging by setting log level to DEBUG in configuration.

## Development

### Adding New Tools

1. Extend `ToolRegistry` class
2. Implement tool function
3. Add to default tools registration
4. Update schemas and documentation

### Customizing LLM Prompts

Modify the prompt construction in `MCPOrchestrator._llm_decision()` method.

### Extending Analysis Workflow

Customize the orchestration logic in `MCPOrchestrator._orchestrate_analysis()` method.

## Deployment

### Requirements

- Python 3.8+
- FastAPI + Uvicorn
- Transformers + Torch (for local models)
- FAISS-CPU or FAISS-GPU
- All existing compliance system dependencies

### Environment Variables

```bash
# Optional: HF Inference API key
HF_API_KEY=your_api_key_here

# Optional: Model cache directory
TRANSFORMERS_CACHE=/path/to/cache
```

### Production Considerations

- Use HF Inference endpoints for production LLM
- Implement proper rate limiting
- Set up monitoring and alerting
- Configure log aggregation
- Use production-grade FAISS deployment

## Integration Points

### Existing Systems

- **Centralized RAG**: Uses existing RAG adapter
- **Evidence System**: Integrates with evidence logger
- **FAISS Index**: Leverages existing vector store
- **Compliance Tools**: Extends existing analyzers

### External APIs

- Hugging Face Model Hub
- Hugging Face Inference Endpoints
- Custom model deployments

## Future Enhancements

1. **Multi-Model Support**: Ensemble multiple LLMs
2. **Advanced Tool Orchestration**: Dynamic tool selection
3. **Real-time Learning**: Continuous model improvement
4. **Advanced Analytics**: Decision pattern analysis
5. **Compliance Templates**: Pre-built analysis workflows

## Support

For issues and questions:

1. Check the test suite output
2. Review service logs
3. Verify configuration settings
4. Test individual components
5. Check system dependencies

## License

This implementation extends the existing compliance system and follows the same licensing terms.
