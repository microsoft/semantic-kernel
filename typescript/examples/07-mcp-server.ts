#!/usr/bin/env node

/**
 * 07-mcp-server.ts (EXPERIMENTAL)
 * 
 * Stand-up an MCP Server that exposes Kernel plugins as MCP tools using the approach 
 * in Microsoft DevBlog. Include client script that calls the tools.
 * 
 * Note: This is a simplified example. Real MCP implementation would require 
 * the @modelcontextprotocol/sdk package.
 * 
 * Usage: OPENAI_API_KEY=your_key_here npx tsx examples/07-mcp-server.ts
 */

import { createServer } from 'http';
import { Kernel } from '../src/index.js';
import { TimePlugin } from './plugins/TimePlugin.js';
import { WeatherPlugin } from './plugins/WeatherPlugin.js';

interface MCPRequest {
  jsonrpc: string;
  id: number;
  method: string;
  params?: any;
}

interface MCPResponse {
  jsonrpc: string;
  id: number;
  result?: any;
  error?: any;
}

class SimpleMCPServer {
  private kernel: Kernel;
  
  constructor() {
    this.kernel = new Kernel();
    
    // Register plugins
    const timePlugin = new TimePlugin();
    const weatherPlugin = new WeatherPlugin();
    this.kernel.addPlugin(timePlugin, 'time');
    this.kernel.addPlugin(weatherPlugin, 'weather');
  }
  
  async handleRequest(request: MCPRequest): Promise<MCPResponse> {
    const { jsonrpc, id, method, params } = request;
    
    try {
      switch (method) {
        case 'tools/list':
          // List available tools
          return {
            jsonrpc,
            id,
            result: {
              tools: [
                {
                  name: 'time.getCurrentTimeUtc',
                  description: 'Get the current time in UTC',
                  inputSchema: { type: 'object', properties: {} }
                },
                {
                  name: 'weather.getCurrentWeather',
                  description: 'Get current weather for a location',
                  inputSchema: {
                    type: 'object',
                    properties: {
                      location: { type: 'string', description: 'Location name' }
                    }
                  }
                }
              ]
            }
          };
          
        case 'tools/call':
          // Execute tool
          const { name, arguments: args } = params;
          const [pluginName, functionName] = name.split('.');
          const kernelFunction = this.kernel.getFunction(pluginName, functionName);
          
          if (!kernelFunction) {
            throw new Error(`Function ${name} not found`);
          }
          
          const context = { variables: args };
          const result = await kernelFunction.invoke(context as any);
          
          return {
            jsonrpc,
            id,
            result: { content: [{ type: 'text', text: result }] }
          };
          
        default:
          throw new Error(`Unknown method: ${method}`);
      }
    } catch (error: any) {
      return {
        jsonrpc,
        id,
        error: { code: -1, message: error.message }
      };
    }
  }
}

async function main() {
  try {
    console.log('🔧 MCP Server (Experimental) - Starting...');
    
    const mcpServer = new SimpleMCPServer();
    
    // Create HTTP server for MCP
    const server = createServer(async (req, res) => {
      if (req.method === 'POST') {
        let body = '';
        req.on('data', chunk => {
          body += chunk.toString();
        });
        
        req.on('end', async () => {
          try {
            const request = JSON.parse(body);
            const response = await mcpServer.handleRequest(request);
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(response));
          } catch (error: any) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: error.message }));
          }
        });
      } else {
        res.writeHead(405);
        res.end();
      }
    });
    
    const port = 3000;
    server.listen(port, () => {
      console.log(`🚀 MCP Server running on http://localhost:${port}`);
    });
    
    // Demo client request
    setTimeout(async () => {
      try {
        console.log('📞 Testing MCP server with client request...');
        
        const testRequest = {
          jsonrpc: '2.0',
          id: 1,
          method: 'tools/list'
        };
        
        const response = await fetch(`http://localhost:${port}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(testRequest)
        });
        
        const result = await response.json();
        console.log('📋 Available tools:', result.result?.tools?.length || 0);
        
        console.log('✅ PASS - MCP server example completed successfully');
        server.close();
      } catch (error: any) {
        console.error('❌ FAIL - Error in MCP server example:', error.message);
        server.close();
        process.exit(1);
      }
    }, 1000);
    
  } catch (error: any) {
    console.error('❌ FAIL - Error in MCP server example:', error.message);
    process.exit(1);
  }
}

main();