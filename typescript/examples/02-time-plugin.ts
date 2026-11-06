#!/usr/bin/env node

/**
 * 02-time-plugin.ts
 * 
 * Port of the Python TimePlugin sample - register plugin, ask "What time is it in UTC +1 h?" 
 * and show the LLM performs the function-call loop.
 * 
 * Usage: OPENAI_API_KEY=your_key_here npx tsx examples/02-time-plugin.ts
 */

import { Kernel, OpenAIChatCompletion } from '../src/index.js';
import { TimePlugin } from './plugins/TimePlugin.js';

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
    
    // Register TimePlugin
    const timePlugin = new TimePlugin();
    kernel.addPlugin(timePlugin, 'time');
    
    console.log('🕒 Asking about time in UTC+1...');
    
    // Ask about time with function calling
    const response = await kernel.chat('What time is it in UTC +1 hour?');
    console.log('🤖 Assistant:', response.content);
    
    console.log('✅ PASS - Time plugin example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in time plugin example:', error.message);
    process.exit(1);
  }
}

main();