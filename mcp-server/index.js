#!/usr/bin/env node

/**
 * Geo-Compliance MCP Server
 * 
 * A Model Context Protocol server that acts as the "front door" to the 
 * compliance-checking pipeline, providing human-in-the-loop capabilities.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { 
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool 
} from '@modelcontextprotocol/sdk/types.js';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import winston from 'winston';

// Initialize logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'mcp-server.log' }),
    new winston.transports.Console({ format: winston.format.simple() })
  ]
});

// Configuration
const PYTHON_ENV = process.env.PYTHON_ENV || '../myenv/bin/python';
const PROJECT_ROOT = process.env.PROJECT_ROOT || '..';
const CONFIDENCE_THRESHOLD = parseFloat(process.env.CONFIDENCE_THRESHOLD || '0.8');
const HUMAN_REVIEW_WEBHOOK = process.env.HUMAN_REVIEW_WEBHOOK;

class ComplianceMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'geo-compliance-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupRequestHandlers();
  }

  setupToolHandlers() {
    // Register compliance analysis tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'retrieve_docs',
            description: 'Retrieve relevant regulatory documents using FAISS + BGE embeddings',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Query to search for in regulatory documents'
                },
                top_k: {
                  type: 'number',
                  description: 'Number of top documents to retrieve',
                  default: 5
                }
              },
              required: ['query']
            }
          },
          {
            name: 'check_compliance',
            description: 'Check compliance of a feature using RAG + LLM analysis',
            inputSchema: {
              type: 'object',
              properties: {
                feature_data: {
                  type: 'object',
                  description: 'Feature data in JSON format to analyze for compliance'
                },
                jurisdiction: {
                  type: 'string',
                  description: 'Target jurisdiction (e.g., "EU", "US", "CA")',
                  default: 'EU'
                }
              },
              required: ['feature_data']
            }
          },
          {
            name: 'primary_llm',
            description: 'Call primary LLM (GPT-4o-mini) for analysis',
            inputSchema: {
              type: 'object',
              properties: {
                prompt: {
                  type: 'string',
                  description: 'Prompt to send to the LLM'
                },
                context: {
                  type: 'string',
                  description: 'Additional context for the LLM'
                }
              },
              required: ['prompt']
            }
          },
          {
            name: 'backup_llm',
            description: 'Call backup LLM (Gemini Flash) for analysis',
            inputSchema: {
              type: 'object',
              properties: {
                prompt: {
                  type: 'string',
                  description: 'Prompt to send to the backup LLM'
                },
                context: {
                  type: 'string',
                  description: 'Additional context for the LLM'
                }
              },
              required: ['prompt']
            }
          },
          {
            name: 'request_human_review',
            description: 'Trigger human review when system abstains or has low confidence',
            inputSchema: {
              type: 'object',
              properties: {
                analysis_context: {
                  type: 'object',
                  description: 'Context of the analysis that needs human review'
                },
                reason: {
                  type: 'string',
                  description: 'Reason for requesting human review',
                  enum: ['low_confidence', 'abstain', 'conflict', 'edge_case']
                },
                priority: {
                  type: 'string',
                  description: 'Priority level for review',
                  enum: ['low', 'medium', 'high', 'urgent'],
                  default: 'medium'
                }
              },
              required: ['analysis_context', 'reason']
            }
          },
          {
            name: 'get_system_status',
            description: 'Get current status of the compliance analysis system',
            inputSchema: {
              type: 'object',
              properties: {},
              additionalProperties: false
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;
        
        logger.info(`Tool called: ${name}`, { args });

        switch (name) {
          case 'retrieve_docs':
            return await this.retrieveDocs(args);
          
          case 'check_compliance':
            return await this.checkCompliance(args);
          
          case 'primary_llm':
            return await this.callPrimaryLLM(args);
          
          case 'backup_llm':
            return await this.callBackupLLM(args);
          
          case 'request_human_review':
            return await this.requestHumanReview(args);
          
          case 'get_system_status':
            return await this.getSystemStatus();
          
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        logger.error(`Tool execution error: ${error.message}`, { error, tool: request.params.name });
        return {
          content: [
            {
              type: 'text',
              text: `Error executing tool: ${error.message}`
            }
          ]
        };
      }
    });
  }

  setupRequestHandlers() {
    // Handle initialization and other MCP protocol messages
    this.server.onerror = (error) => {
      logger.error('MCP Server error:', error);
    };
  }

  async retrieveDocs(args) {
    const { query, top_k = 5 } = args;
    
    try {
      const result = await this.runPythonScript('retrieve_docs.py', {
        query,
        top_k
      });
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              documents: result.documents,
              scores: result.scores,
              metadata: {
                query,
                retrieved_count: result.documents?.length || 0,
                timestamp: new Date().toISOString()
              }
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      logger.error('Error retrieving documents:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              tool: 'retrieve_docs'
            }, null, 2)
          }
        ]
      };
    }
  }

  async checkCompliance(args) {
    const { feature_data, jurisdiction = 'EU' } = args;
    
    try {
      const result = await this.runPythonScript('check_compliance.py', {
        feature_data,
        jurisdiction
      });
      
      // Check if human review is needed
      const needsHumanReview = (
        result.confidence < CONFIDENCE_THRESHOLD ||
        result.verdict === 'ABSTAIN' ||
        result.conflicts?.length > 0
      );
      
      if (needsHumanReview) {
        // Automatically trigger human review
        await this.requestHumanReview({
          analysis_context: {
            feature_data,
            jurisdiction,
            analysis_result: result
          },
          reason: result.confidence < CONFIDENCE_THRESHOLD ? 'low_confidence' : 
                  result.verdict === 'ABSTAIN' ? 'abstain' : 'conflict',
          priority: result.confidence < 0.5 ? 'high' : 'medium'
        });
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              verdict: result.verdict,
              confidence: result.confidence,
              reasoning: result.reasoning,
              citations: result.citations,
              jurisdiction,
              human_review_triggered: needsHumanReview,
              timestamp: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      logger.error('Error checking compliance:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              tool: 'check_compliance'
            }, null, 2)
          }
        ]
      };
    }
  }

  async callPrimaryLLM(args) {
    const { prompt, context } = args;
    
    try {
      const result = await this.runPythonScript('call_llm.py', {
        prompt,
        context,
        model_type: 'primary'
      });
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              response: result.response,
              model_used: result.model_used,
              tokens_used: result.tokens_used,
              timestamp: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      logger.error('Error calling primary LLM:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              tool: 'primary_llm'
            }, null, 2)
          }
        ]
      };
    }
  }

  async callBackupLLM(args) {
    const { prompt, context } = args;
    
    try {
      const result = await this.runPythonScript('call_llm.py', {
        prompt,
        context,
        model_type: 'backup'
      });
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              response: result.response,
              model_used: result.model_used,
              tokens_used: result.tokens_used,
              timestamp: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      logger.error('Error calling backup LLM:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              tool: 'backup_llm'
            }, null, 2)
          }
        ]
      };
    }
  }

  async requestHumanReview(args) {
    const { analysis_context, reason, priority = 'medium' } = args;
    
    try {
      // Log the human review request
      logger.warn('Human review requested', {
        reason,
        priority,
        context: analysis_context
      });
      
      // Save to human review queue
      const reviewRequest = {
        id: `review_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        reason,
        priority,
        context: analysis_context,
        status: 'pending'
      };
      
      await this.saveReviewRequest(reviewRequest);
      
      // Send webhook notification if configured
      if (HUMAN_REVIEW_WEBHOOK) {
        await this.sendWebhookNotification(reviewRequest);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              review_id: reviewRequest.id,
              message: 'Human review requested successfully',
              reason,
              priority,
              webhook_sent: !!HUMAN_REVIEW_WEBHOOK,
              timestamp: reviewRequest.timestamp
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      logger.error('Error requesting human review:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              tool: 'request_human_review'
            }, null, 2)
          }
        ]
      };
    }
  }

  async getSystemStatus() {
    try {
      const status = await this.runPythonScript('system_status.py', {});
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              status: 'healthy',
              components: status,
              mcp_server: {
                version: '1.0.0',
                uptime: process.uptime(),
                memory_usage: process.memoryUsage()
              },
              timestamp: new Date().toISOString()
            }, null, 2)
          }
        ]
      };
    } catch (error) {
      logger.error('Error getting system status:', error);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              tool: 'get_system_status'
            }, null, 2)
          }
        ]
      };
    }
  }

  async runPythonScript(scriptName, args) {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(PROJECT_ROOT, 'mcp-tools', scriptName);
      const python = spawn(PYTHON_ENV, [scriptPath], {
        cwd: PROJECT_ROOT
      });
      
      let stdout = '';
      let stderr = '';
      
      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      python.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python script failed with code ${code}: ${stderr}`));
        } else {
          try {
            const result = JSON.parse(stdout.trim());
            resolve(result);
          } catch (parseError) {
            reject(new Error(`Failed to parse Python script output: ${parseError.message}`));
          }
        }
      });
      
      // Send arguments to Python script via stdin
      python.stdin.write(JSON.stringify(args));
      python.stdin.end();
    });
  }

  async saveReviewRequest(reviewRequest) {
    const reviewsDir = path.join(PROJECT_ROOT, 'human-reviews');
    await fs.mkdir(reviewsDir, { recursive: true });
    
    const filename = `${reviewRequest.id}.json`;
    const filepath = path.join(reviewsDir, filename);
    
    await fs.writeFile(filepath, JSON.stringify(reviewRequest, null, 2));
  }

  async sendWebhookNotification(reviewRequest) {
    if (!HUMAN_REVIEW_WEBHOOK) return;
    
    try {
      const fetch = (await import('node-fetch')).default;
      
      const response = await fetch(HUMAN_REVIEW_WEBHOOK, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: `🚨 Human Review Requested`,
          blocks: [
            {
              type: 'section',
              text: {
                type: 'mrkdwn',
                text: `*Reason:* ${reviewRequest.reason}\n*Priority:* ${reviewRequest.priority}\n*Review ID:* ${reviewRequest.id}`
              }
            }
          ]
        })
      });
      
      if (!response.ok) {
        throw new Error(`Webhook failed: ${response.statusText}`);
      }
      
      logger.info('Webhook notification sent successfully', { reviewId: reviewRequest.id });
    } catch (error) {
      logger.error('Failed to send webhook notification:', error);
    }
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    logger.info('Geo-Compliance MCP Server started successfully');
    logger.info(`Python environment: ${PYTHON_ENV}`);
    logger.info(`Project root: ${PROJECT_ROOT}`);
    logger.info(`Confidence threshold: ${CONFIDENCE_THRESHOLD}`);
    
    // Graceful shutdown
    process.on('SIGINT', async () => {
      logger.info('Shutting down MCP server...');
      await this.server.close();
      process.exit(0);
    });
  }
}

// Start the server
const server = new ComplianceMCPServer();
server.start().catch((error) => {
  logger.error('Failed to start MCP server:', error);
  process.exit(1);
});
