#!/usr/bin/env node

/**
 * 01-quick-chat-mock.ts
 * 
 * CI-friendly version of quick-chat that uses mocked OpenAI responses
 * for testing without requiring real API keys.
 * 
 * Usage: npm run examples:mock
 */

import { Kernel } from '../src/index.js';

// Mock OpenAI chat completion for CI
class MockChatCompletion {
  async completeChat(messages: any[]): Promise<any> {
    // Return a mock response
    return {
      role: 'assistant',
      content: 'Hello! Here\'s a fun fact about TypeScript: TypeScript was created by Microsoft in 2012 and compiles to plain JavaScript, making it easier to catch errors during development while still running anywhere JavaScript runs.'
    };
  }

  async *streamChat(messages: any[]): AsyncIterable<any> {
    yield {
      role: 'assistant',
      content: 'Mock response for streaming',
      functionCall: undefined
    };
  }
}

async function main() {
  try {
    // Create kernel instance
    const kernel = new Kernel();
    
    // Add mock chat completion service for CI testing
    const mockChat = new MockChatCompletion();
    kernel.addService(mockChat, 'chat');
    
    // Single prompt/response
    const response = await kernel.chat('Hello! Tell me a fun fact about TypeScript.');
    console.log('🤖 Assistant:', response.content);
    
    console.log('✅ PASS - Mock quick chat example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in mock quick chat example:', error.message);
    process.exit(1);
  }
}

main();