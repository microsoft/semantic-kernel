#!/usr/bin/env node

/**
 * 01-quick-chat.ts
 * 
 * Minimal "Hello Kernel" 20-line script: create kernel → add OpenAIChatCompletion → single prompt/response.
 * Must work with only an OPENAI_API_KEY set.
 * 
 * Usage: OPENAI_API_KEY=your_key_here npx tsx examples/01-quick-chat.ts
 */

import { Kernel, OpenAIChatCompletion } from '../src/index.js';

async function main() {
  try {
    // Create kernel instance
    const kernel = new Kernel();
    
    // Add OpenAI chat completion service
    const openai = new OpenAIChatCompletion({
      apiKey: process.env.OPENAI_API_KEY,
      model: 'gpt-4o'
    });
    kernel.addService(openai, 'chat');
    
    // Single prompt/response
    const response = await kernel.chat('Hello! Tell me a fun fact about TypeScript.');
    console.log('🤖 Assistant:', response.content);
    
    console.log('✅ PASS - Quick chat example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in quick chat example:', error.message);
    process.exit(1);
  }
}

main();