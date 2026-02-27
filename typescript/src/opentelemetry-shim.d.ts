declare module '@opentelemetry/api' {
  interface Span {
    end(): void;
  }
  interface Tracer {
    startSpan(name: string, options?: any): Span;
  }
  export const trace: {
    getTracer(name: string): Tracer;
  };
}
