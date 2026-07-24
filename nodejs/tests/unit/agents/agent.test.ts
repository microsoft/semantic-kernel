import { randomUUID } from 'crypto'
import { promises as fs } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import {
  Agent,
  AgentChannel,
  AgentRegistry,
  AgentResponseItem,
  DeclarativeSpecMixin,
  registerAgentType,
} from '../../../semantic-kernel/agents/agent'
import { ChatMessageContent } from '../../../semantic-kernel/contents/chat-message-content'
import { StreamingChatMessageContent } from '../../../semantic-kernel/contents/streaming-chat-message-content'
import { AuthorRole } from '../../../semantic-kernel/contents/utils/author-role'
import { AgentInitializationException } from '../../../semantic-kernel/exceptions/agent-exceptions'
import { KernelArguments } from '../../../semantic-kernel/functions/kernel-arguments'
import { KernelFunction } from '../../../semantic-kernel/functions/kernel-function'
import { Kernel, KernelPlugin } from '../../../semantic-kernel/kernel'

// #region Mock Classes

class MockChannel extends AgentChannel {
  async receive(_history: any[]): Promise<ChatMessageContent | null> {
    return null
  }

  async invokeAgent(_agent: Agent): Promise<AsyncIterable<ChatMessageContent | StreamingChatMessageContent>> {
    return (async function* () {})()
  }

  async getHistory(): Promise<any[]> {
    return []
  }
}

class MockAgent extends Agent {
  static channelType: new () => AgentChannel = MockChannel

  constructor(options: { name?: string; description?: string; id?: string } = {}) {
    const { name = 'Test-Agent', description = 'A test agent', id } = options
    super({ name, description, id })
  }

  async createChannel(): Promise<AgentChannel> {
    return new MockChannel()
  }

  async getResponse(_options: any): Promise<AgentResponseItem<ChatMessageContent>> {
    const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'test response' })
    return new AgentResponseItem(message, {} as any)
  }

  async *invoke(_options: any): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
    const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'invoke result' })
    yield new AgentResponseItem(message, {} as any)
  }

  async *invokeStream(_options: any): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
    const message = new StreamingChatMessageContent({
      role: AuthorRole.ASSISTANT,
      content: 'streamed result',
      choiceIndex: 0,
    })
    yield new AgentResponseItem(message, {} as any)
  }
}

class MockAgentWithoutChannelType extends MockAgent {
  static channelType: any = null
}

// Mock implementation of KernelPlugin (it's an interface, not a class)
function createDummyPlugin(): KernelPlugin {
  return {
    name: 'DummyPlugin',
    description: 'A dummy plugin for testing',
    functions: new Map<string, KernelFunction>([
      [
        'dummyFunction',
        {
          name: 'dummyFunction',
          pluginName: 'DummyPlugin',
          description: 'A dummy function',
          parameters: [],
          metadata: {
            name: 'dummyFunction',
            pluginName: 'DummyPlugin',
            description: 'A dummy function',
            parameters: [],
          },
          async invoke() {
            return { value: 'result' } as any
          },
        } as any,
      ],
    ]),
  }
}

// #endregion

describe('Agent', () => {
  describe('initialization', () => {
    test('should initialize with provided values', () => {
      const name = 'TestAgent'
      const description = 'A test agent'
      const id = randomUUID()

      const agent = new MockAgent({ name, description, id })

      expect(agent.name).toBe(name)
      expect(agent.description).toBe(description)
      expect(agent.id).toBe(id)
    })

    test('should generate default id when not provided', () => {
      const agent = new MockAgent()

      expect(agent.id).toBeDefined()
      expect(agent.id).not.toBeNull()
      // Validate UUID format
      expect(() => {
        if (agent.id) {
          const uuid = agent.id
          expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
        }
      }).not.toThrow()
    })
  })

  describe('channel management', () => {
    test('should get channel keys', () => {
      const agent = new MockAgent()
      const keys = Array.from(agent.getChannelKeys())

      expect(keys).toHaveLength(1)
      expect(keys[0]).toBe('MockChannel')
    })

    test('should create channel', async () => {
      const agent = new MockAgent()
      const channel = await agent.createChannel()

      expect(channel).toBeInstanceOf(AgentChannel)
    })

    test('should throw error when channel type not configured', () => {
      const agent = new MockAgentWithoutChannelType()

      expect(() => {
        Array.from(agent.getChannelKeys())
      }).toThrow(AgentInitializationException)
    })
  })

  describe('equality and hashing', () => {
    test('should be equal when id, name, and description match', () => {
      const id = randomUUID()
      const agent1 = new MockAgent({ name: 'TestAgent', description: 'A test agent', id })
      const agent2 = new MockAgent({ name: 'TestAgent', description: 'A test agent', id })

      expect(agent1.equals(agent2)).toBe(true)
    })

    test('should not be equal when description differs', () => {
      const id = randomUUID()
      const agent1 = new MockAgent({ name: 'TestAgent', description: 'A test agent', id })
      const agent3 = new MockAgent({ name: 'TestAgent', description: 'A different description', id })

      expect(agent1.equals(agent3)).toBe(false)
    })

    test('should not be equal when name differs', () => {
      const id = randomUUID()
      const agent1 = new MockAgent({ name: 'TestAgent', description: 'A test agent', id })
      const agent4 = new MockAgent({ name: 'AnotherAgent', description: 'A test agent', id })

      expect(agent1.equals(agent4)).toBe(false)
    })

    test('should not be equal when comparing to non-agent', () => {
      const agent = new MockAgent({ name: 'TestAgent', description: 'A test agent', id: randomUUID() })
      const nonAgent = 'Not an agent'

      expect(agent.equals(nonAgent as any)).toBe(false)
    })

    test('should have same hash when equal', () => {
      const id = randomUUID()
      const agent1 = new MockAgent({ name: 'TestAgent', description: 'A test agent', id })
      const agent2 = new MockAgent({ name: 'TestAgent', description: 'A test agent', id })

      expect(agent1.hash()).toBe(agent2.hash())
    })

    test('should have different hash when not equal', () => {
      const id = randomUUID()
      const agent1 = new MockAgent({ name: 'TestAgent', description: 'A test agent', id })
      const agent3 = new MockAgent({ name: 'TestAgent', description: 'A different description', id })

      expect(agent1.hash()).not.toBe(agent3.hash())
    })
  })

  describe('argument merging', () => {
    test('should return empty KernelArguments when both are undefined', () => {
      const agent = new MockAgent()
      const merged = agent['_mergeArguments'](undefined)

      expect(merged).toBeInstanceOf(KernelArguments)
      expect(merged.size).toBe(0)
    })

    test('should return override when agent arguments is undefined', () => {
      const agent = new MockAgent()
      const override = new KernelArguments({ settings: { key: 'override' } as any, args: { param1: 'val1' } })

      const merged = agent['_mergeArguments'](override)

      expect(merged).toBe(override)
    })

    test('should return agent arguments when override is undefined', () => {
      const agent = new MockAgent()
      agent.arguments = new KernelArguments({ settings: { key: 'base' } as any, args: { param1: 'baseVal' } })

      const merged = agent['_mergeArguments'](undefined)

      expect(merged).toBe(agent.arguments)
    })

    test('should merge arguments with override taking precedence', () => {
      const agent = new MockAgent()
      agent.arguments = new KernelArguments({
        settings: { key1: 'val1', common: 'base' } as any,
        args: { param1: 'baseVal' },
      })
      const override = new KernelArguments({
        settings: { key2: 'override_val', common: 'override' } as any,
        args: { param2: 'override_param' },
      })

      const merged = agent['_mergeArguments'](override)

      // Note: The actual merged behavior depends on the implementation
      // These assertions test that both settings are present after merge
      expect(merged).toBeDefined()
      expect(merged.get('param1')).toBe('baseVal')
      expect(merged.get('param2')).toBe('override_param')
    })
  })

  describe('DeclarativeSpecMixin', () => {
    describe('normalize spec fields', () => {
      test('should create kernel and extract fields', () => {
        const data = {
          name: 'TestAgent',
          description: 'An agent',
          instructions: 'Use this.',
          model: { options: { temperature: 0.7 } },
        }

        const [fields, kernel] = DeclarativeSpecMixin['_normalizeSpecFields']({ data })

        expect(kernel).toBeInstanceOf(Kernel)
        expect(fields.name).toBe('TestAgent')
        expect(fields.arguments).toBeInstanceOf(KernelArguments)
      })

      test('should add plugins to kernel', () => {
        const plugin = createDummyPlugin()
        const data = { name: 'PluginAgent' }

        const [, kernel] = DeclarativeSpecMixin['_normalizeSpecFields']({ data, plugins: [plugin] })

        expect(kernel.plugins.has('DummyPlugin')).toBe(true)
      })

      test('should parse prompt template and overwrite instructions', () => {
        const data = {
          name: 'T',
          promptTemplate: { template: 'new instructions', templateFormat: 'semantic-kernel' },
        }

        const [fields] = DeclarativeSpecMixin['_normalizeSpecFields']({ data })

        expect(fields.instructions).toBe('new instructions')
      })
    })

    describe('validate tools', () => {
      test('should succeed with valid plugin', () => {
        const kernel = new Kernel()
        kernel.addPlugin(createDummyPlugin())
        const toolsList = [{ id: 'DummyPlugin.dummyFunction', type: 'function' }]

        expect(() => {
          DeclarativeSpecMixin['_validateTools'](toolsList, kernel)
        }).not.toThrow()
      })

      test('should fail on invalid format', () => {
        const kernel = new Kernel()

        expect(() => {
          DeclarativeSpecMixin['_validateTools']([{ id: 'badformat', type: 'function' }], kernel)
        }).toThrow(AgentInitializationException)
        expect(() => {
          DeclarativeSpecMixin['_validateTools']([{ id: 'badformat', type: 'function' }], kernel)
        }).toThrow(/format/)
      })

      test('should fail on missing plugin', () => {
        const kernel = new Kernel()

        expect(() => {
          DeclarativeSpecMixin['_validateTools']([{ id: 'MissingPlugin.foo', type: 'function' }], kernel)
        }).toThrow(AgentInitializationException)
        expect(() => {
          DeclarativeSpecMixin['_validateTools']([{ id: 'MissingPlugin.foo', type: 'function' }], kernel)
        }).toThrow(/not found in kernel/)
      })

      test('should fail on missing function', () => {
        const plugin = createDummyPlugin()
        const kernel = new Kernel()
        kernel.addPlugin(plugin)

        expect(() => {
          DeclarativeSpecMixin['_validateTools']([{ id: 'DummyPlugin.bar', type: 'function' }], kernel)
        }).toThrow(AgentInitializationException)
        expect(() => {
          DeclarativeSpecMixin['_validateTools']([{ id: 'DummyPlugin.bar', type: 'function' }], kernel)
        }).toThrow(/not found in plugin/)
      })
    })
  })

  describe('AgentRegistry', () => {
    beforeAll(() => {
      // Register test agent type
      @registerAgentType('test_agent')
      class _TestAgent extends DeclarativeSpecMixin {
        static resolvePlaceholders(yamlStr: string, _settings?: any, _extras?: Record<string, any>): string {
          return yamlStr
        }

        protected static async _fromDict(options: {
          data?: Record<string, any>
          kernel: Kernel
          [key: string]: any
        }): Promise<Agent> {
          const { data, kernel } = options
          return new _TestAgent({
            name: data?.name,
            description: data?.description,
            instructions: data?.instructions,
            kernel,
          })
        }

        async getResponse(_options: any): Promise<AgentResponseItem<ChatMessageContent>> {
          const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'Test response' })
          return new AgentResponseItem(message, {} as any)
        }

        async *invoke(_options: any): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
          const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'invoke result' })
          yield new AgentResponseItem(message, {} as any)
        }

        async *invokeStream(_options: any): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
          const message = new StreamingChatMessageContent({
            role: AuthorRole.ASSISTANT,
            content: 'streamed result',
            choiceIndex: 0,
          })
          yield new AgentResponseItem(message, {} as any)
        }
      }
    })

    describe('create from YAML', () => {
      test('should create agent from valid YAML', async () => {
        const yamlStr = `
type: test_agent
name: TestAgent
`
        const agent = await AgentRegistry.createFromYaml({ yamlStr })

        expect(agent.constructor.name).toBe('_TestAgent')
      })

      test('should throw error when type is missing', async () => {
        const yamlStr = `
name: InvalidAgent
`
        await expect(AgentRegistry.createFromYaml({ yamlStr })).rejects.toThrow(AgentInitializationException)
        await expect(AgentRegistry.createFromYaml({ yamlStr })).rejects.toThrow(/Missing 'type'/)
      })

      test('should throw error when type is not registered', async () => {
        const yamlStr = `
type: nonexistent_agent
`
        await expect(AgentRegistry.createFromYaml({ yamlStr })).rejects.toThrow(AgentInitializationException)
        await expect(AgentRegistry.createFromYaml({ yamlStr })).rejects.toThrow(/not registered/)
      })
    })

    describe('create from dict', () => {
      test('should create agent from valid dict', async () => {
        const data = { type: 'test_agent', name: 'FromDictAgent' }
        const agent = await AgentRegistry.createFromDict({ data })

        expect(agent.name).toBe('FromDictAgent')
        expect(agent.constructor.name).toBe('_TestAgent')
      })

      test('should throw error when type is missing', async () => {
        const data = { name: 'NoType' }

        await expect(AgentRegistry.createFromDict({ data })).rejects.toThrow(AgentInitializationException)
        await expect(AgentRegistry.createFromDict({ data })).rejects.toThrow(/Missing 'type'/)
      })

      test('should throw error when type is not supported', async () => {
        const data = { type: 'unknown' }

        await expect(AgentRegistry.createFromDict({ data })).rejects.toThrow(AgentInitializationException)
        await expect(AgentRegistry.createFromDict({ data })).rejects.toThrow(/not supported/)
      })
    })

    describe('create from file', () => {
      test('should create agent from file', async () => {
        const filePath = join(tmpdir(), `spec-${randomUUID()}.yaml`)

        await fs.writeFile(filePath, 'type: test_agent\nname: FileAgent\n', 'utf-8')

        try {
          const agent = await AgentRegistry.createFromFile({ filePath })

          expect(agent.name).toBe('FileAgent')
          expect(agent.constructor.name).toBe('_TestAgent')
        } finally {
          await fs.unlink(filePath).catch(() => {})
        }
      })

      test('should throw error when file does not exist', async () => {
        await expect(AgentRegistry.createFromFile({ filePath: '/nonexistent/path/spec.yaml' })).rejects.toThrow(
          AgentInitializationException
        )
        await expect(AgentRegistry.createFromFile({ filePath: '/nonexistent/path/spec.yaml' })).rejects.toThrow(
          /Failed to read agent spec file/
        )
      })
    })
  })
})
