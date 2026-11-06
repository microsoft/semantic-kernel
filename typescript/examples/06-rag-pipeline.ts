#!/usr/bin/env node

/**
 * 06-rag-pipeline.ts
 * 
 * 50-line Retrieval-Augmented-Generation pipeline (embed → search → compose prompt).
 * Inspired by RAG blog tutorial.
 * 
 * Usage: OPENAI_API_KEY=your_key_here npx tsx examples/06-rag-pipeline.ts
 */

import { Kernel, OpenAIChatCompletion, InMemoryVectorStore } from '../src/index.js';

// Simple embedding function for demonstration
function createEmbedding(text: string): number[] {
  const words = text.toLowerCase().split(/\W+/).filter(w => w.length > 0);
  const vector = new Array(50).fill(0);
  words.forEach((word, i) => {
    const hash = word.split('').reduce((a, b) => ((a << 5) - a) + b.charCodeAt(0), 0);
    vector[Math.abs(hash) % 50] += 1;
  });
  return vector;
}

async function main() {
  try {
    console.log('🔄 RAG Pipeline: Starting...');
    
    // 1. Setup
    const kernel = new Kernel();
    const openai = new OpenAIChatCompletion({ apiKey: process.env.OPENAI_API_KEY });
    kernel.addService(openai, 'chat');
    
    const vectorStore = new InMemoryVectorStore();
    await vectorStore.createCollection('knowledge');
    
    // 2. Embed & Index documents
    const documents = [
      'Semantic Kernel is an open-source SDK for AI orchestration.',
      'TypeScript provides static typing for JavaScript development.',
      'Vector databases enable semantic search and retrieval.',
      'Large Language Models can process and generate human-like text.',
      'RAG combines retrieval with generation for better responses.'
    ];
    
    console.log('📝 Embedding and indexing documents...');
    for (let i = 0; i < documents.length; i++) {
      await vectorStore.upsert('knowledge', {
        id: `doc-${i}`,
        embedding: createEmbedding(documents[i]),
        metadata: { text: documents[i] }
      });
    }
    
    // 3. Query & Search
    const query = 'How does semantic search work?';
    console.log(`🔍 Searching for: "${query}"`);
    
    const queryEmbedding = createEmbedding(query);
    const results = await vectorStore.getNearestMatches('knowledge', queryEmbedding, 3);
    
    // 4. Compose prompt with context
    const context = results.map(r => r.metadata?.text).join('\n');
    const ragPrompt = `Context:\n${context}\n\nQuestion: ${query}\n\nAnswer:`;
    
    // 5. Generate response
    console.log('🤖 Generating RAG response...');
    const response = await kernel.chat(ragPrompt);
    console.log('📖 RAG Response:', response.content);
    
    console.log('✅ PASS - RAG pipeline example completed successfully');
  } catch (error: any) {
    console.error('❌ FAIL - Error in RAG pipeline example:', error.message);
    process.exit(1);
  }
}

main();