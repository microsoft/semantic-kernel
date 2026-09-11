import { Client } from '@modelcontextprotocol/sdk/client'
import { Tool } from '@modelcontextprotocol/sdk/types.js'
import {
  MCPSsePlugin,
  MCPStdioPlugin,
  MCPStreamableHttpPlugin,
  MCPWebsocketPlugin,
} from '../../../semantic-kernel/connectors/mcp'

// Helper function to create mock tools
function createMockTools(): Tool[] {
  return [
    {
      name: 'func1',
      description: 'func1',
      inputSchema: {
        type: 'object',
        properties: {
          name: { type: 'string' },
        },
        required: ['name'],
      },
    },
    {
      name: 'func2',
      description: 'func2',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
  ]
}

// Helper function to create mock tools with special characters
function createMockToolsWithSpecialChars(): Tool[] {
  return [
    {
      name: 'nasa/get-astronomy-picture',
      description: 'func with slash',
      inputSchema: {
        type: 'object',
        properties: {},
        required: [],
      },
    },
    {
      name: 'weird\\name with spaces',
      description: 'func with backslash and spaces',
      inputSchema: {
        type: 'object',
        properties: {},
        required: [],
      },
    },
  ]
}

// Mock Client class
class MockClient extends Client {
  private mockTools: Tool[]
  private isInitialized: boolean = false

  constructor(tools: Tool[] = createMockTools()) {
    super(
      {
        name: 'test-client',
        version: '1.0.0',
      },
      {
        capabilities: {},
      }
    )
    this.mockTools = tools
  }

  async connect(_transport: any): Promise<void> {
    // Mock connect
    this.isInitialized = true
  }

  async listTools(): Promise<{ tools: Tool[] }> {
    return { tools: this.mockTools }
  }

  async close(): Promise<void> {
    this.isInitialized = false
  }

  getIsInitialized(): boolean {
    return this.isInitialized
  }
}

describe('MCP Plugin Tests', () => {
  describe('MCPStdioPlugin', () => {
    test('should create plugin with command and args', async () => {
      const mockClient = new MockClient()
      const plugin = new MCPStdioPlugin({
        name: 'TestMCPPlugin',
        description: 'Test MCP Plugin',
        command: 'uv',
        args: ['--directory', 'path', 'run', 'file.py'],
        client: mockClient,
      })

      try {
        // Mock the transport creation
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        expect(plugin.name).toBe('TestMCPPlugin')
        expect(plugin.description).toBe('Test MCP Plugin')
        expect(plugin.command).toBe('uv')
        expect(plugin.args).toEqual(['--directory', 'path', 'run', 'file.py'])

        // Check that functions were created from tools
        // Functions are attached directly to the plugin instance
        expect((plugin as any).func1).toBeDefined()
        expect(typeof (plugin as any).func1).toBe('function')

        expect((plugin as any).func2).toBeDefined()
        expect(typeof (plugin as any).func2).toBe('function')
      } finally {
        await plugin.close()
      }
    })

    test('should create plugin without connecting', async () => {
      const plugin = new MCPStdioPlugin({
        name: 'test',
        command: 'echo',
        args: ['hello'],
      })

      // Should be able to create the plugin
      expect(plugin.name).toBe('test')
      expect(plugin.command).toBe('echo')
      expect(plugin.args).toEqual(['hello'])
    })
  })

  describe('MCPSsePlugin', () => {
    test('should create plugin with URL', async () => {
      const mockClient = new MockClient()
      const plugin = new MCPSsePlugin({
        name: 'TestMCPPlugin',
        description: 'Test MCP Plugin',
        url: 'http://localhost:8080/sse',
        client: mockClient,
      })

      try {
        // Mock the transport creation
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        expect(plugin.name).toBe('TestMCPPlugin')
        expect(plugin.description).toBe('Test MCP Plugin')
        expect(plugin.url).toBe('http://localhost:8080/sse')

        // Check that functions were created from tools
        expect((plugin as any).func1).toBeDefined()
        expect((plugin as any).func2).toBeDefined()
      } finally {
        await plugin.close()
      }
    })

    test('should not initialize session if already initialized', async () => {
      const mockClient = new MockClient()
      // Simulate already initialized client
      ;(mockClient as any).isInitialized = true

      const plugin = new MCPSsePlugin({
        name: 'test',
        url: 'http://localhost:8080/sse',
        client: mockClient,
      })

      try {
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        // Client should already be initialized
        expect(mockClient.getIsInitialized()).toBe(true)
      } finally {
        await plugin.close()
      }
    })
  })

  describe('MCPStreamableHttpPlugin', () => {
    test('should create plugin with URL and options', async () => {
      const mockClient = new MockClient()
      const plugin = new MCPStreamableHttpPlugin({
        name: 'TestMCPPlugin',
        description: 'Test MCP Plugin',
        url: 'http://localhost:8080/mcp',
        client: mockClient,
      })

      try {
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        expect(plugin.name).toBe('TestMCPPlugin')
        expect(plugin.url).toBe('http://localhost:8080/mcp')

        // Check that functions were created from tools
        expect((plugin as any).func1).toBeDefined()
        expect((plugin as any).func2).toBeDefined()
      } finally {
        await plugin.close()
      }
    })
  })

  describe('MCPWebsocketPlugin', () => {
    test('should create plugin with websocket URL', async () => {
      const mockClient = new MockClient()
      const plugin = new MCPWebsocketPlugin({
        name: 'TestMCPPlugin',
        description: 'Test MCP Plugin',
        url: 'ws://localhost:8080/websocket',
        client: mockClient,
      })

      try {
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        expect(plugin.name).toBe('TestMCPPlugin')
        expect(plugin.url).toBe('ws://localhost:8080/websocket')

        // Check that functions were created from tools
        expect((plugin as any).func1).toBeDefined()
        expect((plugin as any).func2).toBeDefined()
      } finally {
        await plugin.close()
      }
    })
  })

  describe('MCP Tool Name Normalization', () => {
    test('should normalize tool names with special characters', async () => {
      const mockClient = new MockClient(createMockToolsWithSpecialChars())
      const plugin = new MCPSsePlugin({
        name: 'TestMCPPlugin',
        description: 'Test MCP Plugin',
        url: 'http://localhost:8080/sse',
        client: mockClient,
      })

      try {
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        // The normalized names should exist as functions on the plugin
        expect((plugin as any)['nasa-get-astronomy-picture']).toBeDefined()
        expect((plugin as any)['weird-name-with-spaces']).toBeDefined()

        // Original names with invalid characters should NOT exist
        expect((plugin as any)['nasa/get-astronomy-picture']).toBeUndefined()
        expect((plugin as any)['weird\\name with spaces']).toBeUndefined()

        // Get all function names from the plugin
        const functionNames = Object.keys(plugin).filter(
          (key) =>
            typeof (plugin as any)[key] === 'function' && (plugin as any)[key].__kernel_function_name__ !== undefined
        )

        // Verify all names match the allowed pattern
        for (const name of functionNames) {
          expect(name).toMatch(/^[A-Za-z0-9_.-]+$/)
        }
      } finally {
        await plugin.close()
      }
    })
  })

  describe('Plugin Integration with Kernel', () => {
    test('should add plugin to kernel and access functions', async () => {
      const mockClient = new MockClient()
      const plugin = new MCPSsePlugin({
        name: 'TestMCPPlugin',
        description: 'Test MCP Plugin',
        url: 'http://localhost:8080/sse',
        client: mockClient,
      })

      try {
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        expect(plugin.name).toBe('TestMCPPlugin')
        expect(plugin.description).toBe('Test MCP Plugin')

        // Check functions exist on the plugin
        const func1 = (plugin as any).func1
        expect(func1).toBeDefined()
        expect(typeof func1).toBe('function')
        expect(func1.__kernel_function_name__).toBe('func1')

        const func2 = (plugin as any).func2
        expect(func2).toBeDefined()
        expect(typeof func2).toBe('function')
        expect(func2.__kernel_function_name__).toBe('func2')

        // Check function parameters from metadata
        const func1Params = func1.__kernel_function_parameters__ || []
        expect(func1Params.length).toBe(1)
        expect(func1Params[0].name).toBe('name')
        expect(func1Params[0].is_required).toBe(true)

        const func2Params = func2.__kernel_function_parameters__ || []
        expect(func2Params.length).toBe(0)
      } finally {
        await plugin.close()
      }
    })
  })

  describe('Function Parameter Validation', () => {
    test('should correctly parse function parameters from inputSchema', async () => {
      const mockTools: Tool[] = [
        {
          name: 'complexFunc',
          description: 'A function with multiple parameters',
          inputSchema: {
            type: 'object',
            properties: {
              requiredParam: { type: 'string' },
              optionalParam: { type: 'number' },
              boolParam: { type: 'boolean' },
            },
            required: ['requiredParam'],
          },
        },
      ]

      const mockClient = new MockClient(mockTools)
      const plugin = new MCPSsePlugin({
        name: 'TestPlugin',
        url: 'http://localhost:8080/sse',
        client: mockClient,
      })

      try {
        jest.spyOn(plugin as any, 'createTransport').mockResolvedValue({
          async start() {},
          async close() {},
          async send() {},
          onmessage: null,
          onerror: null,
          onclose: null,
        })

        await plugin.connect()

        const func = (plugin as any).complexFunc
        expect(func).toBeDefined()

        const params = func.__kernel_function_parameters__ || []
        expect(params.length).toBe(3)

        const requiredParam = params.find((p: any) => p.name === 'requiredParam')
        expect(requiredParam?.is_required).toBe(true)

        const optionalParam = params.find((p: any) => p.name === 'optionalParam')
        expect(optionalParam?.is_required).toBe(false)

        const boolParam = params.find((p: any) => p.name === 'boolParam')
        expect(boolParam?.is_required).toBe(false)
      } finally {
        await plugin.close()
      }
    })
  })
})
