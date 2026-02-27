import { IService, KernelFunction, KernelFunctionMetadata } from './types';
import { VectorMemoryStore } from './memory';
import { getKernelFunctionMeta } from './decorators';
import { Context } from './context';
import { Logger, ConsoleLogger } from './logger';
import { trace } from '@opentelemetry/api';

export interface KernelConfig {
  memoryStore?: VectorMemoryStore;
  logger?: Logger;
}

export class Kernel {
  private services = new Map<string, IService>();
  private plugins = new Map<string, Map<string, KernelFunction>>();
  private memoryStore?: VectorMemoryStore;
  private logger: Logger;
  
  constructor(config: KernelConfig = {}) {
    this.logger = config.logger ?? new ConsoleLogger();
    if (config.memoryStore) {
      this.registerMemoryStore(config.memoryStore);
    }
  }

  addService(service: IService, id?: string): void {
    const key = id ?? (service as any).id ?? service.constructor.name;
    this.services.set(key, service);
  }

  getLogger(): Logger {
    return this.logger;
  }

  registerMemoryStore(store: VectorMemoryStore, id = 'memory'): void {
    this.memoryStore = store;
    this.addService(store, id);
  }

  addPlugin(instance: object, pluginName: string): void {
    const functions = new Map<string, KernelFunction>();
    const proto = Object.getPrototypeOf(instance);
    const names = Object.getOwnPropertyNames(proto);

    for (const name of names) {
      if (name === 'constructor') continue;
      const fn = (instance as any)[name];
      if (typeof fn !== 'function') continue;
      const meta: KernelFunctionMetadata | undefined = getKernelFunctionMeta(fn);
      const funcName = meta?.name ?? name;
      const kfunc: KernelFunction = {
        pluginName,
        name: funcName,
        description: meta?.description,
        parameters: meta?.parameters,
        invoke: (ctx: Context) => fn.call(instance, ctx),
      };
      functions.set(funcName, kfunc);
    }

    this.plugins.set(pluginName, functions);
  }

  getService<T extends IService>(id: string): T | undefined {
    return this.services.get(id) as T | undefined;
  }

  get memory(): VectorMemoryStore | undefined {
    return this.memoryStore;
  }

  getFunction(pluginName: string, name: string): KernelFunction | undefined {
    return this.plugins.get(pluginName)?.get(name);
  }

  private getChatService(): import('./types').IChatCompletionClient | undefined {
    for (const svc of this.services.values()) {
      if (
        typeof (svc as any).completeChat === 'function' &&
        typeof (svc as any).streamChat === 'function'
      ) {
        return svc as any;
      }
    }
    return undefined;
  }

  async chat(prompt: string, options: import('./types').ChatCompletionSettings = {}): Promise<import('./types').ChatMessage> {
    const chat = this.getChatService();
    if (!chat) throw new Error('No chat completion service');

    const messages: import('./types').ChatMessage[] = [
      { role: 'user', content: prompt },
    ];

    // build function defs if supported
    const funcs: any[] = [];
    for (const [pname, fmap] of this.plugins) {
      for (const [fname, kfunc] of fmap) {
        if (!kfunc.parameters) continue;
        const params: any = { type: 'object', properties: {} };
        for (const param of kfunc.parameters) {
          params.properties[param.name] = param.schema ?? {};
        }
        funcs.push({
          name: `${pname}.${fname}`,
          description: kfunc.description,
          parameters: params,
        });
      }
    }

    if (funcs.length) {
      options.functions = funcs;
      options.functionCall = options.functionCall ?? 'auto';
    }

    while (true) {
      const useStream = options.stream ?? false;
      let msg: import('./types').ChatMessage;
      if (useStream) {
        let full: import('./types').ChatMessage = { role: 'assistant', content: '', };
        for await (const part of chat.streamChat(messages, options)) {
          if (part.content) full.content = (full.content ?? '') + part.content;
          if (part.functionCall) {
            full.functionCall = full.functionCall || { name: '', arguments: '' };
            if (part.functionCall.name)
              full.functionCall.name += part.functionCall.name;
            if (part.functionCall.arguments)
              full.functionCall.arguments += part.functionCall.arguments;
          }
        }
        msg = full;
      } else {
        msg = await chat.completeChat(messages, options);
      }

      if (msg.functionCall) {
        const [plugin, func] = msg.functionCall.name.split('.');
        const kfunc = this.getFunction(plugin, func);
        if (!kfunc)
          throw new Error(`Function ${msg.functionCall.name} not found`);
        const args = msg.functionCall.arguments
          ? JSON.parse(msg.functionCall.arguments)
          : {};
        const span = trace
          .getTracer('semantic-kernel')
          .startSpan('Kernel.RunFunction', {
            attributes: { plugin, function: func },
          });
        this.logger.info('run function', { plugin, function: func });
        let result;
        try {
          result = await kfunc.invoke(new Context(this, args));
        } finally {
          span.end();
        }
        messages.push({
          role: 'assistant',
          content: null,
          functionCall: msg.functionCall,
        });
        messages.push({
          role: 'function',
          name: msg.functionCall.name,
          content: JSON.stringify(result),
        });
        continue;
      }

      messages.push(msg);
      return msg;
    }
  }
}
