import OpenAI from 'openai';
import {
  IChatCompletionClient,
  ChatMessage,
  ChatCompletionSettings,
} from './types';
import { z } from 'zod';
import { Logger, ConsoleLogger } from './logger';
import { trace } from '@opentelemetry/api';

export const OpenAIClientConfigSchema = z.object({
  apiKey: z.string({ required_error: 'OpenAI API key missing' }).min(1, {
    message: 'OpenAI API key missing',
  }),
  model: z.string().min(1).default('gpt-4o'),
});

export interface OpenAIClientConfig {
  apiKey?: string;
  model?: string;
  logger?: Logger;
}

export class OpenAIChatCompletion implements IChatCompletionClient {
  private client: OpenAI;
  private model: string;
  private logger: Logger;
  private tracer = trace.getTracer('semantic-kernel');

  constructor(config: OpenAIClientConfig = {}) {
    const env = (globalThis as any).process?.env ?? {};
    const parsed = OpenAIClientConfigSchema.safeParse({
      apiKey: config.apiKey ?? env.OPENAI_API_KEY,
      model: config.model ?? env.OPENAI_MODEL,
    });
    if (!parsed.success) {
      const message = parsed.error.issues.map((i) => i.message).join(', ');
      throw new Error(`Invalid OpenAI configuration: ${message}`);
    }
    this.model = parsed.data.model;
    this.client = new OpenAI({ apiKey: parsed.data.apiKey });
    this.logger = config.logger ?? new ConsoleLogger();
  }

  async completeChat(
    messages: ChatMessage[],
    settings: ChatCompletionSettings = {}
  ): Promise<ChatMessage> {
    const span = this.tracer.startSpan('LLM.Completion', {
      attributes: { model: settings.model ?? this.model },
    });
    const response = await this.client.chat.completions.create({
      model: settings.model ?? this.model,
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
        name: m.name,
        function_call: m.functionCall,
      })),
      temperature: settings.temperature,
      max_tokens: settings.maxTokens,
      functions: settings.functions,
      function_call: settings.functionCall,
    } as any);
    this.logger.debug('llm completion', { model: settings.model ?? this.model });
    span.end();
    const msg: any = response.choices[0].message;
    return {
      role: msg.role as ChatMessage['role'],
      content: msg.content ?? null,
      name: msg.name,
      functionCall: msg.function_call,
    };
  }

  async *streamChat(
    messages: ChatMessage[],
    settings: ChatCompletionSettings = {}
  ): AsyncIterable<ChatMessage> {
    const span = this.tracer.startSpan('LLM.Completion', {
      attributes: { model: settings.model ?? this.model },
    });
    const stream = await this.client.chat.completions.create({
      model: settings.model ?? this.model,
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
        name: m.name,
        function_call: m.functionCall,
      })),
      temperature: settings.temperature,
      max_tokens: settings.maxTokens,
      stream: true,
      functions: settings.functions,
      function_call: settings.functionCall,
    } as any);
    this.logger.debug('llm completion', { model: settings.model ?? this.model });
    for await (const part of stream as any) {
      const delta = part.choices[0]?.delta;
      if (!delta) continue;
      yield {
        role: 'assistant',
        content: delta.content ?? null,
        functionCall: delta.function_call,
      } as ChatMessage;
    }
    span.end();
  }
}
