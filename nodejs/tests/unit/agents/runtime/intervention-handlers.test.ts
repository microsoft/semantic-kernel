import { Agent } from '../../../../semantic-kernel/agents/runtime/core/agent'
import { AgentId, CoreAgentId } from '../../../../semantic-kernel/agents/runtime/core/agent-id'
import { AgentMetadata } from '../../../../semantic-kernel/agents/runtime/core/agent-metadata'
import { MessageDroppedException } from '../../../../semantic-kernel/agents/runtime/core/exceptions'
import { DropMessage, InterventionHandler } from '../../../../semantic-kernel/agents/runtime/core/intervention'
import { MessageContext } from '../../../../semantic-kernel/agents/runtime/core/message-context'
import { TopicId } from '../../../../semantic-kernel/agents/runtime/core/topic'
import { InProcessRuntime } from '../../../../semantic-kernel/agents/runtime/in-process/in-process-runtime'

class TestAgent implements Agent {
  constructor(
    public readonly id: AgentId,
    public readonly metadata: AgentMetadata
  ) {}

  async onMessage(message: any, _ctx: MessageContext): Promise<any> {
    return { echo: message }
  }

  async close(): Promise<void> {
    // No-op
  }

  async saveState(): Promise<Record<string, any>> {
    return {}
  }

  async loadState(_state: Record<string, any>): Promise<void> {
    // No-op
  }
}

class MessageLogger implements InterventionHandler {
  public sentMessages: any[] = []
  public publishedMessages: any[] = []
  public responseMessages: any[] = []

  async onSend(message: any, _messageContext: MessageContext, _recipient: AgentId): Promise<any | typeof DropMessage> {
    this.sentMessages.push(message)
    return message
  }

  async onPublish(message: any, _messageContext: MessageContext): Promise<any | typeof DropMessage> {
    this.publishedMessages.push(message)
    return message
  }

  async onResponse(message: any, _sender: AgentId, _recipient: AgentId | null): Promise<any | typeof DropMessage> {
    this.responseMessages.push(message)
    return message
  }
}

class MessageDropper implements InterventionHandler {
  async onSend(_message: any, _messageContext: MessageContext, _recipient: AgentId): Promise<any | typeof DropMessage> {
    return DropMessage
  }

  async onPublish(_message: any, _messageContext: MessageContext): Promise<any | typeof DropMessage> {
    return DropMessage
  }

  async onResponse(_message: any, _sender: AgentId, _recipient: AgentId | null): Promise<any | typeof DropMessage> {
    return DropMessage
  }
}

class MessageTransformer implements InterventionHandler {
  async onSend(message: any, _messageContext: MessageContext, _recipient: AgentId): Promise<any | typeof DropMessage> {
    return { ...message, transformed: true }
  }

  async onPublish(message: any, _messageContext: MessageContext): Promise<any | typeof DropMessage> {
    return { ...message, transformed: true }
  }

  async onResponse(message: any, _sender: AgentId, _recipient: AgentId | null): Promise<any | typeof DropMessage> {
    return { ...message, transformed: true }
  }
}

describe('Intervention Handlers', () => {
  let runtime: InProcessRuntime

  describe('MessageLogger', () => {
    let logger: MessageLogger

    beforeEach(() => {
      logger = new MessageLogger()
      runtime = new InProcessRuntime({ interventionHandlers: [logger] })
    })

    test('should log sent messages', async () => {
      const agentId = new CoreAgentId('test-agent', 'default')
      await runtime.registerFactory(
        'test-agent',
        () => new TestAgent(agentId, { type: 'test-agent', key: 'default', description: 'Test agent' })
      )
      runtime.start()

      const message = { text: 'Hello' }
      await runtime.sendMessage(message, agentId)

      await runtime.stopWhenIdle()

      expect(logger.sentMessages).toContain(message)
      expect(logger.sentMessages.length).toBe(1)
    })

    test('should log published messages', async () => {
      const agentId = new CoreAgentId('test-agent', 'default')
      const topicId = new TopicId('test', 'test-topic')

      await runtime.registerFactory(
        'test-agent',
        () => new TestAgent(agentId, { type: 'test-agent', key: 'default', description: 'Test agent' })
      )
      await runtime.addSubscription({
        id: 'sub-1',
        isMatch: () => true,
        mapToAgent: () => agentId,
        equals: (other) => other.id === 'sub-1',
      })

      runtime.start()

      const message = { text: 'Broadcast' }
      await runtime.publishMessage(message, topicId)

      await runtime.stopWhenIdle()

      expect(logger.publishedMessages).toContain(message)
    })
  })

  describe('MessageDropper', () => {
    beforeEach(() => {
      runtime = new InProcessRuntime({ interventionHandlers: [new MessageDropper()] })
    })

    test('should drop sent messages', async () => {
      const agentId = new CoreAgentId('test-agent', 'default')
      await runtime.registerFactory(
        'test-agent',
        () => new TestAgent(agentId, { type: 'test-agent', key: 'default', description: 'Test agent' })
      )
      runtime.start()

      const message = { text: 'Hello' }
      const responsePromise = runtime.sendMessage(message, agentId)

      await expect(responsePromise).rejects.toThrow(MessageDroppedException)
      await runtime.stopWhenIdle()
    })

    test('should drop published messages', async () => {
      const agentId = new CoreAgentId('test-agent', 'default')
      const topicId = new TopicId('test', 'test-topic')

      await runtime.registerFactory(
        'test-agent',
        () => new TestAgent(agentId, { type: 'test-agent', key: 'default', description: 'Test agent' })
      )
      await runtime.addSubscription({
        id: 'sub-1',
        isMatch: () => true,
        mapToAgent: () => agentId,
        equals: (other) => other.id === 'sub-1',
      })

      runtime.start()

      const message = { text: 'Broadcast' }
      await runtime.publishMessage(message, topicId)

      // The publish should complete but the message should not be delivered
      await runtime.stopWhenIdle()
      // No error thrown, message just dropped silently
    })
  })

  describe('MessageTransformer', () => {
    beforeEach(() => {
      runtime = new InProcessRuntime({ interventionHandlers: [new MessageTransformer()] })
    })

    test('should transform sent messages', async () => {
      const agentId = new CoreAgentId('test-agent', 'default')
      let receivedMessage: any = null

      await runtime.registerFactory(
        'test-agent',
        () =>
          new (class extends TestAgent {
            async onMessage(message: any, ctx: MessageContext): Promise<any> {
              receivedMessage = message
              return super.onMessage(message, ctx)
            }
          })(agentId, { type: 'test-agent', key: 'default', description: 'Test agent' })
      )

      runtime.start()

      const message = { text: 'Hello' }
      await runtime.sendMessage(message, agentId)

      await runtime.stopWhenIdle()

      expect(receivedMessage).toEqual({ text: 'Hello', transformed: true })
    })
  })

  describe('Multiple handlers', () => {
    test('should apply handlers in order', async () => {
      const logger = new MessageLogger()
      const transformer = new MessageTransformer()

      runtime = new InProcessRuntime({ interventionHandlers: [logger, transformer] })

      const agentId = new CoreAgentId('test-agent', 'default')
      let receivedMessage: any = null

      await runtime.registerFactory(
        'test-agent',
        () =>
          new (class extends TestAgent {
            async onMessage(message: any, ctx: MessageContext): Promise<any> {
              receivedMessage = message
              return super.onMessage(message, ctx)
            }
          })(agentId, { type: 'test-agent', key: 'default', description: 'Test agent' })
      )

      runtime.start()

      const message = { text: 'Hello' }
      await runtime.sendMessage(message, agentId)

      await runtime.stopWhenIdle()

      // Logger should see original message
      expect(logger.sentMessages[0]).toEqual({ text: 'Hello' })
      // Agent should receive transformed message
      expect(receivedMessage).toEqual({ text: 'Hello', transformed: true })
    })
  })
})
