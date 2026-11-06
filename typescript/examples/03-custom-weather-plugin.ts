#!/usr/bin/env node

/**
 * 03-custom-weather-plugin.ts
 * 
 * Re-implement the "OpenAI function-calling with custom WeatherPlugin" demo in TS 
 * (auto-generated JSON schema, looping until final answer).
 * 
 * Usage: OPENAI_API_KEY=your_key_here npx tsx examples/03-custom-weather-plugin.ts
 */

import { Kernel, OpenAIChatCompletion } from '../src/index.js';
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
    
    // Register WeatherPlugin
    const weatherPlugin = new WeatherPlugin();
    kernel.addPlugin(weatherPlugin, 'weather');
    
    console.log('🌤️ Asking about weather with function calling...');
    
    // Ask about weather with function calling
    const response = await kernel.chat('What\'s the weather like in New York today?');
    console.log('🤖 Assistant:', response.content);
    
    console.log('✅ PASS - Weather plugin example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in weather plugin example:', error.message);
    process.exit(1);
  }
}

main();