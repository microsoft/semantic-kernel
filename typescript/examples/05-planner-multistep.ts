#!/usr/bin/env node

/**
 * 05-planner-multistep.ts
 * 
 * Complex user goal ("plan my Saturday itinerary") showing multi-turn function-calling loop 
 * with two plugins (Time & Weather). Confirms planning logic from Task 4.
 * 
 * Usage: OPENAI_API_KEY=your_key_here npx tsx examples/05-planner-multistep.ts
 */

import { Kernel, OpenAIChatCompletion } from '../src/index.js';
import { TimePlugin } from './plugins/TimePlugin.js';
import { WeatherPlugin } from './plugins/WeatherPlugin.js';

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
    
    // Register plugins
    const timePlugin = new TimePlugin();
    const weatherPlugin = new WeatherPlugin();
    kernel.addPlugin(timePlugin, 'time');
    kernel.addPlugin(weatherPlugin, 'weather');
    
    console.log('📅 Planning Saturday itinerary with multi-step function calling...');
    
    // Complex planning request that should trigger multiple function calls
    const planningPrompt = `
      Help me plan my Saturday itinerary in New York. 
      I want to know:
      1. What time it is now
      2. What the weather will be like
      3. Based on the time and weather, suggest some activities
      
      Please use the available functions to get current information.
    `;
    
    const response = await kernel.chat(planningPrompt);
    console.log('🤖 Assistant:', response.content);
    
    console.log('✅ PASS - Multi-step planner example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in multi-step planner example:', error.message);
    process.exit(1);
  }
}

main();