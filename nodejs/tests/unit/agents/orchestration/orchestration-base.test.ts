import { Agent, AgentResponseItem } from '../../../../semantic-kernel/agents/agent'
import {
    OrchestrationBase,
    OrchestrationResult,
} from '../../../../semantic-kernel/agents/orchestration/orchestration-base'
import { CancellationToken } from '../../../../semantic-kernel/agents/runtime/core/cancellation-token'
import { CoreRuntime } from '../../../../semantic-kernel/agents/runtime/core/core-runtime'
import { ChatMessageContent } from '../../../../semantic-kernel/contents/chat-message-content'
import { StreamingChatMessageContent } from '../../../../semantic-kernel/contents/streaming-chat-message-content'
import { AuthorRole } from '../../../../semantic-kernel/contents/utils/author-role'

// Mock classes for testing
class MockAgent extends Agent {
  async getResponse(_options: any): Promise<AgentResponseItem<ChatMessageContent>> {
    const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'mock response' })
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

// Test implementation of OrchestrationBase
class TestOrchestration<TIn = any, TOut = any> extends OrchestrationBase<TIn, TOut> {
  protected async _start(): Promise<void> {
    // Test implementation
  }

  protected async _prepare(): Promise<void> {
    // Test implementation
  }
}

describe('OrchestrationBase', () => {
  describe('initialization', () => {
    test('should initialize with provided values', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({
        members: [agent],
        name: 'TestOrch',
        description: 'Test orchestration',
      })
      expect(orch.name).toBe('TestOrch')
      expect(orch.description).toBe('Test orchestration')
    })

    test('should initialize with default values', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      expect(orch.name).toContain('TestOrchestration_')
      expect(orch.description).toBe('A multi-agent orchestration.')
    })

    test('should throw error with no members', () => {
      expect(() => new TestOrchestration({ members: [] })).toThrow('The members list cannot be empty.')
    })
  })

  describe('type handling', () => {
    test('should set types correctly', () => {
      // Test with default types
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      expect(orch).toBeInstanceOf(OrchestrationBase)
    })

    test('should create with custom types', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      expect(orch).toBeInstanceOf(OrchestrationBase)
    })
  })

  describe('invoke method', () => {
    test('should invoke with string input', async () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      const runtime = {} as CoreRuntime
      const result = await orch.invoke('test task', runtime)
      expect(result).toBeInstanceOf(OrchestrationResult)
      expect(result.cancellationToken).toBeInstanceOf(CancellationToken)
    })

    test('should invoke with ChatMessageContent input', async () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      const runtime = {} as CoreRuntime
      const message = new ChatMessageContent({ role: AuthorRole.USER, content: 'test' })
      const result = await orch.invoke(message, runtime)
      expect(result).toBeInstanceOf(OrchestrationResult)
    })

    test('should invoke with ChatMessageContent array input', async () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      const runtime = {} as CoreRuntime
      const messages = [new ChatMessageContent({ role: AuthorRole.USER, content: 'test' })]
      const result = await orch.invoke(messages, runtime)
      expect(result).toBeInstanceOf(OrchestrationResult)
    })

    test('should invoke with custom type', async () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration<any, any>({ members: [agent] })
      const runtime = {} as CoreRuntime
      const customInput = { field: 'value' }
      const result = await orch.invoke(customInput, runtime)
      expect(result).toBeInstanceOf(OrchestrationResult)
    })

    test('should invoke with custom type and async input transform', async () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const inputTransform = async (input: any) => {
        return new ChatMessageContent({ role: AuthorRole.USER, content: JSON.stringify(input) })
      }
      const orch = new TestOrchestration<any, any>({ members: [agent], inputTransform })
      const runtime = {} as CoreRuntime
      const customInput = { field: 'value' }
      const result = await orch.invoke(customInput, runtime)
      expect(result).toBeInstanceOf(OrchestrationResult)
    })
  })

  describe('default input transform', () => {
    test('should transform default type alias correctly', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      // Test with ChatMessageContent
      const message = new ChatMessageContent({ role: AuthorRole.USER, content: 'test' })
      const result = (orch as any)._defaultInputTransform(message)
      expect(result).toBe(message)
      // Test with ChatMessageContent array
      const messages = [message]
      const arrayResult = (orch as any)._defaultInputTransform(messages)
      expect(arrayResult).toBe(messages)
    })

    test('should transform custom type correctly', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      // Test with plain object
      const customInput = { field: 'value' }
      const result = (orch as any)._defaultInputTransform(customInput)
      expect(result).toBeInstanceOf(ChatMessageContent)
      expect(result.content).toBe(JSON.stringify(customInput))
    })

    test('should throw error with incorrect custom type', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      // Test with invalid type (null)
      expect(() => (orch as any)._defaultInputTransform(null)).toThrow(TypeError)
    })
  })

  describe('default output transform', () => {
    test('should transform default type alias correctly', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      // Test with ChatMessageContent
      const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'test' })
      const result = (orch as any)._defaultOutputTransform(message)
      expect(result).toBe(message)
      // Test with ChatMessageContent array
      const messages = [message]
      const arrayResult = (orch as any)._defaultOutputTransform(messages)
      expect(arrayResult).toBe(messages)
    })

    test('should transform custom type correctly', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      // _defaultOutputTransform returns ChatMessageContent as-is when input is ChatMessageContent
      const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'test response' })
      const result = (orch as any)._defaultOutputTransform(message)
      expect(result).toBe(message)
    })

    test('should throw error with incorrect custom type', () => {
      const agent = new MockAgent({ id: 'test', name: 'Test Agent' })
      const orch = new TestOrchestration({ members: [agent] })
      // Test with invalid type
      expect(() => (orch as any)._defaultOutputTransform('invalid')).toThrow(TypeError)
    })
  })

  describe('orchestration result', () => {
    test('should timeout when result not set', async () => {
      const result = new OrchestrationResult()
      await expect(result.get(100)).rejects.toThrow('Timeout waiting for result')
    })

    test('should handle cancellation before completion', async () => {
      const result = new OrchestrationResult()
      result.cancel()
      await expect(result.get()).rejects.toThrow('The invocation was canceled before it could complete.')
    })

    test('should throw error on double cancel', async () => {
      const result = new OrchestrationResult()
      result.cancel()
      expect(() => result.cancel()).toThrow('The invocation has already been canceled.')
    })
  })
})
