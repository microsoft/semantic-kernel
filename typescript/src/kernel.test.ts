import { Kernel } from './kernel.js';

describe('Kernel', () => {
  let kernel: Kernel;

  beforeEach(() => {
    kernel = new Kernel();
  });

  test('should create a kernel instance', () => {
    expect(kernel).toBeInstanceOf(Kernel);
  });

  test('should have a logger', () => {
    const logger = kernel.getLogger();
    expect(logger).toBeDefined();
    expect(logger).toHaveProperty('debug');
    expect(logger).toHaveProperty('info');
    expect(logger).toHaveProperty('warn');
    expect(logger).toHaveProperty('error');
  });

  test('should add services', () => {
    const mockService = {
      id: 'test-service',
      someMethod: () => 'test'
    };

    kernel.addService(mockService, 'test');
    const retrievedService = kernel.getService('test');
    
    expect(retrievedService).toBe(mockService);
  });

  test('should add plugins', () => {
    class TestPlugin {
      testMethod() {
        return 'test result';
      }
    }

    const plugin = new TestPlugin();
    kernel.addPlugin(plugin, 'test-plugin');

    const func = kernel.getFunction('test-plugin', 'testMethod');
    expect(func).toBeDefined();
    expect(func?.name).toBe('testMethod');
    expect(func?.pluginName).toBe('test-plugin');
  });
});