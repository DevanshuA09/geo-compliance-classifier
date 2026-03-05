import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Loader2, Send, Bot, User, CheckCircle, XCircle, Clock } from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  requestId?: string;
}

interface ToolUsage {
  name: string;
  inputs: Record<string, any>;
  output: string;
  duration_ms: number;
  status: string;
  error_message?: string;
}

interface MCPResponse {
  request_id: string;
  decision_flag: boolean;
  confidence: number;
  reasoning_text: string;
  related_regulations: string[];
  tools_used: ToolUsage[];
  retrieval_metadata: Record<string, any>;
  model_metadata: Record<string, any>;
  timings_ms: Record<string, number>;
  evidence_record_path: string;
  timestamp_iso: string;
}

interface MCPRequest {
  feature_id: string;
  feature_title: string;
  description: string;
  artifacts?: string[];
  region_hint?: string;
  dataset_tag?: string;
}

export function MCPChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<MCPResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Parse the input to extract feature information
      const request = parseFeatureRequest(inputValue);
      
      const response = await fetch('/mcp/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const mcpResponse: MCPResponse = await response.json();
      setCurrentResponse(mcpResponse);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: formatResponse(mcpResponse),
        timestamp: new Date(),
        requestId: mcpResponse.request_id,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to analyze feature'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const parseFeatureRequest = (input: string): MCPRequest => {
    // Simple parsing - in practice, this could be more sophisticated
    const lines = input.split('\n').filter(line => line.trim());
    
    return {
      feature_id: `feature_${Date.now()}`,
      feature_title: lines[0] || 'Untitled Feature',
      description: lines.slice(1).join('\n') || input,
      region_hint: input.toLowerCase().includes('eu') ? 'EU' : 
                  input.toLowerCase().includes('california') || input.toLowerCase().includes('ca') ? 'US-CA' :
                  input.toLowerCase().includes('florida') || input.toLowerCase().includes('fl') ? 'US-FL' : undefined,
    };
  };

  const formatResponse = (response: MCPResponse): string => {
    const decision = response.decision_flag ? 'NEEDS geo-specific logic' : 'DOES NOT need geo-specific logic';
    const confidence = (response.confidence * 100).toFixed(1);
    
    return `**Decision**: ${decision}\n\n**Confidence**: ${confidence}%\n\n**Reasoning**: ${response.reasoning_text}\n\n**Related Regulations**: ${response.related_regulations.join(', ')}`;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Card className="flex-1">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            MCP Compliance Chat
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col h-full">
          <ScrollArea className="flex-1 mb-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.type === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {message.type === 'user' ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                      <span className="text-sm opacity-75">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Analyzing feature...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Describe your feature (e.g., 'Age verification for EU users\nRequires parental consent for users under 16')"
              className="flex-1"
              disabled={isLoading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tools Used Visualization */}
      {currentResponse && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Tools Used</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {currentResponse.tools_used.map((tool, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant={tool.status === 'success' ? 'default' : 'destructive'}>
                        {tool.status}
                      </Badge>
                      <span className="font-medium">{tool.name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Clock className="h-3 w-3" />
                      {tool.duration_ms}ms
                    </div>
                  </div>
                  
                  {tool.status === 'success' ? (
                    <div className="text-sm text-gray-600">
                      <div className="font-medium mb-1">Output:</div>
                      <div className="bg-gray-50 rounded p-2 text-xs">
                        {tool.output.length > 200 
                          ? `${tool.output.substring(0, 200)}...` 
                          : tool.output}
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-red-600">
                      <div className="font-medium mb-1">Error:</div>
                      <div>{tool.error_message}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div className="mt-4 pt-4 border-t">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Total Time:</span> {currentResponse.timings_ms.total_ms}ms
                </div>
                <div>
                  <span className="font-medium">Request ID:</span> {currentResponse.request_id}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
