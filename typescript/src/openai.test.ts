import { describe, test, expect } from '@jest/globals';
import { OpenAIClientConfigSchema } from './openai.js';

describe('OpenAI Configuration', () => {
  test('should default to gpt-4o model', () => {
    const result = OpenAIClientConfigSchema.safeParse({
      apiKey: 'test-api-key'
    });
    
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.model).toBe('gpt-4o');
    }
  });

  test('should allow custom model override', () => {
    const result = OpenAIClientConfigSchema.safeParse({
      apiKey: 'test-api-key',
      model: 'gpt-3.5-turbo'
    });
    
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.model).toBe('gpt-3.5-turbo');
    }
  });

  test('should require api key', () => {
    const result = OpenAIClientConfigSchema.safeParse({});
    
    expect(result.success).toBe(false);
  });
});