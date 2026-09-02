import { Kernel } from './kernel';
import { trace } from '@opentelemetry/api';

export class Context {
  variables: Record<string, any>;
  memory?: import('./memory').VectorMemoryStore;
  constructor(public kernel: Kernel, variables: Record<string, any> = {}) {
    this.variables = { ...variables };
    this.memory = kernel.memory;
  }

  async call(plugin: string, func: string, args: Record<string, any> = {}) {
    const kfunc = this.kernel.getFunction(plugin, func);
    if (!kfunc) {
      throw new Error(`Function ${plugin}.${func} not found`);
    }
    const ctx = new Context(this.kernel, args);
    const span = trace
      .getTracer('semantic-kernel')
      .startSpan('Kernel.RunFunction', {
        attributes: { plugin, function: func },
      });
    this.kernel.getLogger().info('run function', { plugin, function: func });
    try {
      return await kfunc.invoke(ctx);
    } finally {
      span.end();
    }
  }
}
