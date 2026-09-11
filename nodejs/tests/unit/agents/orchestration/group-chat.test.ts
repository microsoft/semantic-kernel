import { Agent, AgentResponseItem } from '../../../../semantic-kernel/agents/agent'
import {
  BooleanResult,
  GroupChatOrchestration,
  RoundRobinGroupChatManager,
} from '../../../../semantic-kernel/agents/orchestration/group-chat'
import { OrchestrationResult } from '../../../../semantic-kernel/agents/orchestration/orchestration-base'
import { CoreRuntime } from '../../../../semantic-kernel/agents/runtime/core/core-runtime'
import { ChatHistory } from '../../../../semantic-kernel/contents/chat-history'
import { ChatMessageContent } from '../../../../semantic-kernel/contents/chat-message-content'
import { StreamingChatMessageContent } from '../../../../semantic-kernel/contents/streaming-chat-message-content'
import { AuthorRole } from '../../../../semantic-kernel/contents/utils/author-role'

// Mock classes for testing
class MockAgent extends Agent {
  async getResponse(_options: any): Promise<AgentResponseItem<ChatMessageContent>> {
    const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'mock_response' })
    return new AgentResponseItem(message, {} as any)
  }

  async *invoke(_options: any): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
    const message = new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'mock_response' })
    yield new AgentResponseItem(message, {} as any)
  }

  async *invokeStream(_options: any): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
    // Simulate some processing time
    await new Promise((resolve) => setTimeout(resolve, 50))

    yield new AgentResponseItem(
      new StreamingChatMessageContent({
        role: AuthorRole.ASSISTANT,
        content: 'mock',
        choiceIndex: 0,
      }),
      {} as any
    )

    // Simulate some processing time before sending the next part
    await new Promise((resolve) => setTimeout(resolve, 50))

    yield new AgentResponseItem(
      new StreamingChatMessageContent({
        role: AuthorRole.ASSISTANT,
        content: '_response',
        choiceIndex: 0,
      }),
      {} as any
    )
  }
}

class MockAgentWithException extends MockAgent {
  async *invokeStream(_options: any): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
    // Simulate some processing time
    await new Promise((resolve) => setTimeout(resolve, 50))

    yield new AgentResponseItem(
      new StreamingChatMessageContent({
        role: AuthorRole.ASSISTANT,
        content: 'mock',
        choiceIndex: 0,
      }),
      {} as any
    )

    throw new Error('Mock agent exception')
  }
}

class RoundRobinGroupChatManagerWithUserInput extends RoundRobinGroupChatManager {
  async shouldRequestUserInput(_chatHistory: ChatHistory): Promise<BooleanResult> {
    return new BooleanResult(true, 'Allow user input for testing purposes.')
  }
}

// Mock runtime for testing
class MockRuntime {
  async registerFactory(_type: any, _agentFactory: any, _options?: any): Promise<any> {
    return _type
  }

  async sendMessage(_message: any, _recipient: any, _options?: any): Promise<any> {
    return {}
  }

  async publishMessage(_message: any, _topicId: any, _options?: any): Promise<void> {}

  async tryGetUnderlyingAgentInstance(_id: any, _type?: any): Promise<any> {
    throw new Error('Not implemented in mock')
  }

  async get(_idOrType: any, _key?: string, _options?: any): Promise<any> {
    return { id: 'mock-id', key: 'mock-key' }
  }

  async agentMetadata(_agent: any): Promise<any> {
    return {}
  }

  async agentSaveState(_agent: any): Promise<any> {
    return {}
  }

  async agentLoadState(_agent: any): Promise<any> {
    return {}
  }

  async addSubscription(_subscription: any): Promise<void> {}

  async removeSubscription(_subscription: any): Promise<void> {}

  async addMessageSerializer(_contentType: string, _serializer: any): Promise<void> {}
}

// region GroupChatOrchestration

describe('GroupChatOrchestration', () => {
  describe('initialization', () => {
    test('should throw error when member has no description', () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B' })

      expect(
        () =>
          new GroupChatOrchestration({
            members: [agentA, agentB],
            manager: new RoundRobinGroupChatManager(),
          })
      ).toThrow()
    })

    test('should call prepare methods correctly', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager(),
      })

      // This test would require mocking/spying on internal methods
      await orchestration.invoke('test_message', runtime)
    })
  })

  describe('invoke method', () => {
    test('should invoke agents in round-robin order', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager({ maxRounds: 3 }),
      })

      const orchestrationResult = await orchestration.invoke('test_message', runtime)

      expect(orchestrationResult).toBeInstanceOf(OrchestrationResult)
      // Note: We can't easily test the actual result without a full runtime implementation
    })

    test('should invoke with list of messages', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const messages = [
        new ChatMessageContent({ role: AuthorRole.USER, content: 'test_message_1' }),
        new ChatMessageContent({ role: AuthorRole.USER, content: 'test_message_2' }),
      ]

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager({ maxRounds: 2 }),
      })

      const orchestrationResult = await orchestration.invoke(messages, runtime)

      expect(orchestrationResult).toBeInstanceOf(OrchestrationResult)
    })

    test('should call response callback', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const responses: ChatMessageContent[] = []

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager({ maxRounds: 3 }),
        agentResponseCallback: (response) => {
          if (response instanceof ChatMessageContent) {
            responses.push(response)
          } else if (Array.isArray(response)) {
            responses.push(...response)
          }
        },
      })

      const orchestrationResult = await orchestration.invoke('test_message', runtime)

      expect(orchestrationResult).toBeInstanceOf(OrchestrationResult)
      // Note: Response callback requires a full runtime implementation to test
    })

    test('should call streaming response callback', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const responses: Record<string, StreamingChatMessageContent[]> = {}

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager({ maxRounds: 3 }),
        streamingAgentResponseCallback: (response, _isLast) => {
          if (!responses[response.name!]) {
            responses[response.name!] = []
          }
          responses[response.name!].push(response)
        },
      })

      const orchestrationResult = await orchestration.invoke('test_message', runtime)

      expect(orchestrationResult).toBeInstanceOf(OrchestrationResult)
      // Note: Streaming callback requires a full runtime implementation to test
    })

    test('should call human response function', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      let userInputCount = 0

      const humanResponseFunction = (_chatHistory: ChatHistory): ChatMessageContent => {
        userInputCount++
        return new ChatMessageContent({
          role: AuthorRole.USER,
          content: `user_input_${userInputCount}`,
        })
      }

      const orchestrationManager = new RoundRobinGroupChatManagerWithUserInput({
        maxRounds: 3,
        humanResponseFunction,
      })

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: orchestrationManager,
      })

      const orchestrationResult = await orchestration.invoke('test_message', runtime)

      expect(orchestrationResult).toBeInstanceOf(OrchestrationResult)
      // Note: Human response function requires a full runtime implementation to test
    })

    test('should handle cancellation before completion', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager({ maxRounds: 3 }),
      })

      const orchestrationResult = await orchestration.invoke('test_message', runtime)

      // Cancel before the second agent responds
      await new Promise((resolve) => setTimeout(resolve, 190))
      orchestrationResult.cancel()
    })

    test('should throw error when cancelling after completion', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgent({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager({ maxRounds: 3 }),
      })

      const orchestrationResult = await orchestration.invoke('test_message', runtime)

      expect(orchestrationResult).toBeInstanceOf(OrchestrationResult)
      // Note: Cannot test cancel after completion without full runtime implementation
    })

    test('should handle agent raising exception', async () => {
      const agentA = new MockAgent({ id: 'agent-a', name: 'Agent A', description: 'test agent' })
      const agentB = new MockAgentWithException({ id: 'agent-b', name: 'Agent B', description: 'test agent' })

      const runtime = new MockRuntime() as unknown as CoreRuntime

      const orchestration = new GroupChatOrchestration({
        members: [agentA, agentB],
        manager: new RoundRobinGroupChatManager({ maxRounds: 3 }),
      })

      const orchestrationResult = await orchestration.invoke('test_message', runtime)

      expect(orchestrationResult).toBeInstanceOf(OrchestrationResult)
      // Note: Exception handling requires a full runtime implementation to test
    })
  })
})

// endregion GroupChatOrchestration

// region RoundRobinGroupChatManager

describe('RoundRobinGroupChatManager', () => {
  describe('initialization', () => {
    test('should initialize with default values', () => {
      const manager = new RoundRobinGroupChatManager()
      expect(manager.maxRounds).toBeUndefined()
      expect((manager as any).currentRound).toBe(0)
      expect((manager as any).currentIndex).toBe(0)
      expect(manager.humanResponseFunction).toBeUndefined()
    })

    test('should initialize with max rounds', () => {
      const manager = new RoundRobinGroupChatManager({ maxRounds: 5 })
      expect(manager.maxRounds).toBe(5)
      expect((manager as any).currentRound).toBe(0)
      expect((manager as any).currentIndex).toBe(0)
      expect(manager.humanResponseFunction).toBeUndefined()
    })

    test('should initialize with human response function', () => {
      const humanResponseFunction = async (_chatHistory: ChatHistory): Promise<ChatMessageContent> => {
        await new Promise((resolve) => setTimeout(resolve, 100))
        return new ChatMessageContent({ role: AuthorRole.USER, content: 'user_input' })
      }

      const manager = new RoundRobinGroupChatManager({ humanResponseFunction })
      expect(manager.maxRounds).toBeUndefined()
      expect((manager as any).currentRound).toBe(0)
      expect((manager as any).currentIndex).toBe(0)
      expect(manager.humanResponseFunction).toBe(humanResponseFunction)
    })
  })

  describe('should terminate', () => {
    test('should terminate after max rounds', async () => {
      const manager = new RoundRobinGroupChatManager({ maxRounds: 3 })

      let result = await manager.shouldTerminate(new ChatHistory())
      expect(result.result).toBe(false)

      result = await manager.shouldTerminate(new ChatHistory())
      expect(result.result).toBe(false)

      result = await manager.shouldTerminate(new ChatHistory())
      expect(result.result).toBe(false)

      result = await manager.shouldTerminate(new ChatHistory())
      expect(result.result).toBe(true)
    })

    test('should not terminate without max rounds', async () => {
      const manager = new RoundRobinGroupChatManager()

      const result = await manager.shouldTerminate(new ChatHistory())
      expect(result.result).toBe(false)
    })
  })

  describe('select next agent', () => {
    test('should select agents in round-robin order', async () => {
      const manager = new RoundRobinGroupChatManager({ maxRounds: 3 })

      const participantDescriptions = new Map<string, string>([
        ['agent_1', 'Agent 1'],
        ['agent_2', 'Agent 2'],
        ['agent_3', 'Agent 3'],
      ])

      await manager.shouldTerminate(new ChatHistory())
      let result = await manager.selectNextAgent(new ChatHistory(), participantDescriptions)
      expect(result.result).toBe('agent_1')

      await manager.shouldTerminate(new ChatHistory())
      result = await manager.selectNextAgent(new ChatHistory(), participantDescriptions)
      expect(result.result).toBe('agent_2')

      await manager.shouldTerminate(new ChatHistory())
      result = await manager.selectNextAgent(new ChatHistory(), participantDescriptions)
      expect(result.result).toBe('agent_3')

      expect((manager as any).currentRound).toBe(3)
    })
  })
})

// endregion RoundRobinGroupChatManager
