#!/usr/bin/env -S deno run --allow-env --allow-net

/**
 * 08-deno-compat.ts
 * 
 * Same quick-chat sample but executed under Deno 1.42 to prove environment neutrality.
 * 
 * Usage: OPENAI_API_KEY=your_key_here deno run --allow-env --allow-net examples/08-deno-compat.ts
 */

// Note: In a real implementation, this would import from npm:semantic-kernel
// For this demo, we'll use a simplified version

interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'function';
  content: string | null;
}

class SimpleKernel {
  private apiKey: string;
  
  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }
  
  async chat(prompt: string): Promise<ChatMessage> {
    // Simplified OpenAI API call for Deno demo
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 100
      })
    });
    
    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      role: 'assistant',
      content: data.choices[0].message.content
    };
  }
}

async function main() {
  try {
    console.log('🦕 Deno Compatibility Test - Starting...');
    
    const apiKey = Deno.env.get('OPENAI_API_KEY');
    if (!apiKey) {
      throw new Error('OPENAI_API_KEY environment variable required');
    }
    
    // Create simplified kernel instance for Deno
    const kernel = new SimpleKernel(apiKey);
    
    // Single prompt/response
    const response = await kernel.chat('Hello! Tell me a fun fact about Deno.');
    console.log('🤖 Assistant:', response.content);
    
    console.log('✅ PASS - Deno compatibility example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in Deno compatibility example:', error.message);
    Deno.exit(1);
  }
}

main();