#!/usr/bin/env node

/**
 * 04-memory-rag.ts
 * 
 * Demonstrate vector memory: create in-memory store → upsert three text snippets → 
 * query for semantically similar text → feed retrieved context back into LLM for an answer.
 * Mirrors Python sample 06-memory-and-embeddings.ipynb.
 * 
 * Usage: OPENAI_API_KEY=your_key_here npx tsx examples/04-memory-rag.ts
 */

import { Kernel, OpenAIChatCompletion, InMemoryVectorStore } from '../src/index.js';

// Mock embedding function for demonstration (in real implementation, use OpenAI embeddings)
function mockEmbedding(text: string): number[] {
  const hash = text.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a;
  }, 0);
  
  // Generate a simple 10-dimensional vector based on text hash
  const vector = [];
  for (let i = 0; i < 10; i++) {
    vector.push(Math.sin(hash + i) * 0.5 + 0.5);
  }
  return vector;
}

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
    
    // Create and register memory store
    const memoryStore = new InMemoryVectorStore();
    kernel.registerMemoryStore(memoryStore);
    
    console.log('📚 Setting up vector memory with sample documents...');
    
    // Create collection and upsert sample documents
    await memoryStore.createCollection('documents');
    
    const sampleDocs = [
      {
        id: 'doc1',
        text: 'TypeScript is a strongly typed programming language that builds on JavaScript.',
        embedding: mockEmbedding('TypeScript is a strongly typed programming language that builds on JavaScript.')
      },
      {
        id: 'doc2', 
        text: 'Machine learning involves algorithms that improve automatically through experience.',
        embedding: mockEmbedding('Machine learning involves algorithms that improve automatically through experience.')
      },
      {
        id: 'doc3',
        text: 'React is a JavaScript library for building user interfaces.',
        embedding: mockEmbedding('React is a JavaScript library for building user interfaces.')
      }
    ];
    
    for (const doc of sampleDocs) {
      await memoryStore.upsert('documents', {
        id: doc.id,
        embedding: doc.embedding,
        metadata: { text: doc.text }
      });
    }
    
    console.log('🔍 Searching for similar documents...');
    
    // Query for similar documents
    const queryText = 'Tell me about programming languages';
    const queryEmbedding = mockEmbedding(queryText);
    const results = await memoryStore.getNearestMatches('documents', queryEmbedding, 2);
    
    console.log(`Found ${results.length} similar documents:`);
    results.forEach((result, index) => {
      console.log(`  ${index + 1}. ${result.metadata?.text}`);
    });
    
    // Create context from retrieved documents
    const context = results.map(r => r.metadata?.text).join('\n\n');
    const promptWithContext = `Based on this context:\n\n${context}\n\nQuestion: ${queryText}`;
    
    console.log('🤖 Generating response with retrieved context...');
    
    // Get LLM response with context
    const response = await kernel.chat(promptWithContext);
    console.log('🤖 Assistant:', response.content);
    
    console.log('✅ PASS - Memory RAG example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in memory RAG example:', error.message);
    process.exit(1);
  }
}

main();