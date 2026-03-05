# Geo-Compliance MCP Server

A **Model Context Protocol (MCP) server** that acts as the "front door" to your geo-compliance classification pipeline, providing seamless integration with human-in-the-loop workflows.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Node.js dependencies
cd mcp-server
npm install

# Install Python dependencies (if not already installed)
cd ..
pip install streamlit psutil
```

### 2. Configure Environment

```bash
# Copy environment template
cp mcp-server/.env.template mcp-server/.env

# Edit .env with your API keys and settings
```

### 3. Start the MCP Server

```bash
cd mcp-server
npm start
```

### 4. Test the Server

```bash
npm test
```

## 🔧 MCP Tools Available

The server exposes 6 main tools for compliance analysis:

### 1. `retrieve_docs`
Retrieve relevant regulatory documents using FAISS + BGE embeddings.

**Parameters:**
- `query` (string): Search query
- `top_k` (number, optional): Number of documents to retrieve (default: 5)

### 2. `check_compliance`
Full compliance analysis using RAG + LLM pipeline.

**Parameters:**
- `feature_data` (object): Feature data to analyze
- `jurisdiction` (string, optional): Target jurisdiction (default: "EU")

**Automatic Human Review Triggers:**
- Confidence < 0.8
- Verdict = "ABSTAIN"
- Conflicting analysis results

### 3. `primary_llm`
Call primary LLM (GPT-4o-mini) for analysis.

**Parameters:**
- `prompt` (string): Prompt text
- `context` (string, optional): Additional context

### 4. `backup_llm`
Call backup LLM (Gemini Flash) for analysis.

**Parameters:**
- `prompt` (string): Prompt text
- `context` (string, optional): Additional context

### 5. `request_human_review`
Manually trigger human review process.

**Parameters:**
- `analysis_context` (object): Context requiring review
- `reason` (string): Reason for review ("low_confidence", "abstain", "conflict", "edge_case")
- `priority` (string, optional): Priority level ("low", "medium", "high", "urgent")

### 6. `get_system_status`
Get current system health and component status.

## 🔄 Human-in-the-Loop Workflow

### Automatic Triggers
The system automatically requests human review when:
- AI confidence < configured threshold (default: 0.8)
- AI verdict is "ABSTAIN"
- Conflicting analysis results detected

### Review Process
1. **Detection**: System identifies case needing human input
2. **Logging**: Review request saved to `../human-reviews/`
3. **Notification**: Webhook sent (if configured)
4. **Dashboard**: Human reviewer uses Streamlit dashboard
5. **Decision**: Human provides verdict, confidence, and reasoning
6. **Storage**: Decision saved and integrated into system

### Dashboard Access
```bash
# Start human review dashboard
cd mcp-server
streamlit run human_review_dashboard.py
```

## 🔗 Integration Options

### VS Code with MCP Extension
1. Install MCP extension in VS Code
2. Add server configuration to VS Code settings:

```json
{
  "mcp.servers": {
    "geo-compliance": {
      "command": "node",
      "args": ["path/to/mcp-server/index.js"],
      "env": {
        "PYTHON_ENV": "path/to/your/python/env",
        "PROJECT_ROOT": "path/to/project/root"
      }
    }
  }
}
```

### Claude Desktop
Add to Claude Desktop configuration:

```json
{
  "mcpServers": {
    "geo-compliance": {
      "command": "node",
      "args": ["path/to/mcp-server/index.js"],
      "env": {
        "PYTHON_ENV": "path/to/your/python/env",
        "PROJECT_ROOT": "path/to/project/root"
      }
    }
  }
}
```

### Custom Clients
Use the MCP SDK to build custom clients:

```javascript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';

const client = new Client(/* config */);
await client.connect(/* transport */);

// Call compliance check
const result = await client.request(
  { method: 'tools/call' },
  {
    name: 'check_compliance',
    arguments: {
      feature_data: { /* your feature data */ },
      jurisdiction: 'EU'
    }
  }
);
```

## ⚙️ Configuration

### Environment Variables
- `PYTHON_ENV`: Path to Python executable
- `PROJECT_ROOT`: Path to project root directory
- `CONFIDENCE_THRESHOLD`: Minimum confidence for auto-approval (0.0-1.0)
- `HUMAN_REVIEW_WEBHOOK`: Slack/Discord webhook URL for notifications
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_API_KEY`: Google API key
- `HUGGINGFACE_API_KEY`: HuggingFace API key

### Webhook Notifications
Configure Slack webhook for real-time notifications:

1. Create Slack webhook URL
2. Set `HUMAN_REVIEW_WEBHOOK` environment variable
3. Notifications sent automatically for human review requests

## 📊 Monitoring & Logging

### Logs
- MCP server logs: `mcp-server/mcp-server.log`
- Python tool logs: Console output
- Review requests: `human-reviews/*.json`

### Health Checks
Use `get_system_status` tool to monitor:
- LLM handler status
- RAG system status
- FAISS index availability
- Environment configuration
- Python package dependencies
- System metrics (CPU, memory, disk)

## 🛠️ Development

### Adding New Tools
1. Create Python script in `mcp-tools/`
2. Add tool definition to `index.js`
3. Implement handler in `ComplianceMCPServer` class
4. Update documentation

### Testing
```bash
# Run full test suite
npm test

# Test individual tools
node -e "
const client = /* MCP client setup */;
const result = await client.request(
  { method: 'tools/call' },
  { name: 'your_tool', arguments: {} }
);
console.log(result);
"
```

## 🔧 Troubleshooting

### Common Issues

**MCP Server won't start:**
- Check Node.js version (requires v18+)
- Verify Python environment path
- Check environment variables

**Python tools failing:**
- Verify Python environment has required packages
- Check file permissions on `mcp-tools/*.py`
- Review Python logs for import errors

**Human review not triggering:**
- Check confidence threshold setting
- Verify webhook URL (if configured)
- Check `human-reviews/` directory permissions

**LLM calls failing:**
- Verify API keys in `.env`
- Check network connectivity
- Review rate limits and quotas

### Debug Mode
Set environment variable for verbose logging:
```bash
export MCP_LOG_LEVEL=debug
npm start
```

## 📈 Performance Optimization

### Response Time
- Typical tool call: < 2 seconds
- Full compliance analysis: < 5 seconds
- RAG retrieval: < 1 second

### Scaling
- Use Redis for review queue (production)
- Implement connection pooling for LLM calls
- Add caching layer for frequently accessed documents

## 🚀 Deployment

### Local Development
```bash
npm run dev  # Auto-restart on changes
```

### Production
```bash
# Use PM2 for process management
npm install -g pm2
pm2 start index.js --name geo-compliance-mcp
```

### Docker
```dockerfile
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

## 📚 API Reference

### Tool Call Format
```json
{
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  }
}
```

### Response Format
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"success\": true, \"result\": \"...\"}"
    }
  ]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request with documentation updates

## 📄 License

MIT License - see LICENSE file for details.

---

**Ready to revolutionize compliance analysis with human-AI collaboration!** 🚀
