export interface Logger {
  debug(message: string, data?: Record<string, any>): void;
  info(message: string, data?: Record<string, any>): void;
  warn(message: string, data?: Record<string, any>): void;
  error(message: string, data?: Record<string, any>): void;
}

export class ConsoleLogger implements Logger {
  debug(message: string, data?: Record<string, any>): void {
    console.debug(JSON.stringify({ level: 'debug', message, ...data }));
  }
  info(message: string, data?: Record<string, any>): void {
    console.info(JSON.stringify({ level: 'info', message, ...data }));
  }
  warn(message: string, data?: Record<string, any>): void {
    console.warn(JSON.stringify({ level: 'warn', message, ...data }));
  }
  error(message: string, data?: Record<string, any>): void {
    console.error(JSON.stringify({ level: 'error', message, ...data }));
  }
}
