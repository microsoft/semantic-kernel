export interface IService {}

export interface KernelParameter {
  name: string;
  schema?: Record<string, any>;
}

export interface KernelFunctionMetadata {
  name?: string;
  description?: string;
  parameters?: KernelParameter[];
}

export interface KernelFunction {
  pluginName: string;
  name: string;
  description?: string;
  parameters?: KernelParameter[];
  invoke: (context: import('./context').Context) => Promise<any> | any;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'function';
  content: string | null;
  name?: string;
  functionCall?: { name: string; arguments: string };
}

export interface ChatCompletionSettings {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
  functions?: any[];
  functionCall?: 'auto' | { name: string };
}

export interface IChatCompletionClient extends IService {
  completeChat(
    messages: ChatMessage[],
    settings?: ChatCompletionSettings
  ): Promise<ChatMessage>;
  streamChat(
    messages: ChatMessage[],
    settings?: ChatCompletionSettings
  ): AsyncIterable<ChatMessage>;
}
