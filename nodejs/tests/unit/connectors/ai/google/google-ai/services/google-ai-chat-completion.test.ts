import { FunctionChoiceBehavior } from '../../../../../../../semantic-kernel/connectors/ai/function-choice-behavior'
import { GoogleAIChatPromptExecutionSettings } from '../../../../../../../semantic-kernel/connectors/ai/google/google-ai/google-ai-prompt-execution-settings'
import { GoogleAISettings } from '../../../../../../../semantic-kernel/connectors/ai/google/google-ai/google-ai-settings'
import { GoogleAIChatCompletion } from '../../../../../../../semantic-kernel/connectors/ai/google/google-ai/services/google-ai-chat-completion'
import { ChatHistory } from '../../../../../../../semantic-kernel/contents/chat-history'
import { AuthorRole } from '../../../../../../../semantic-kernel/contents/utils/author-role'
import { FinishReason } from '../../../../../../../semantic-kernel/contents/utils/finish-reason'
import { ServiceInitializationError } from '../../../../../../../semantic-kernel/exceptions/service-exceptions'
import { Kernel } from '../../../../../../../semantic-kernel/kernel'

// Mock response types
interface Part {
  text?: string
  functionCall?: {
    name: string
    args: Record<string, any>
  }
}

interface Candidate {
  index?: number
  content?: {
    role?: string
    parts: Part[]
  }
  finish_reason?: string
  safety_ratings?: any[]
  token_count?: number
}

interface GenerateContentResponse {
  candidates: Candidate[]
  prompt_feedback?: any
  usage_metadata?: {
    prompt_token_count?: number
    candidates_token_count?: number
  }
}

describe('GoogleAIChatCompletion', () => {
  const originalEnv = process.env

  beforeEach(() => {
    jest.resetModules()
    process.env = {
      ...originalEnv,
      GOOGLE_AI_GEMINI_MODEL_ID: 'test-gemini-model-id',
      GOOGLE_AI_EMBEDDING_MODEL_ID: 'test-embedding-model-id',
      GOOGLE_AI_API_KEY: 'test-api-key',
      GOOGLE_AI_CLOUD_PROJECT_ID: 'test-project-id',
      GOOGLE_AI_CLOUD_REGION: 'test-region',
    }
  })

  afterAll(() => {
    process.env = originalEnv
  })

  describe('initialization', () => {
    it('should initialize with environment variables', () => {
      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
      })

      expect(service.aiModelId).toBe('test-gemini-model-id')
      expect(service.serviceId).toBe('test-gemini-model-id')
      expect(service.serviceSettings).toBeInstanceOf(GoogleAISettings)
      expect(service.serviceSettings.geminiModelId).toBe('test-gemini-model-id')
      expect(service.serviceSettings.apiKey).toBe('test-api-key')
    })

    it('should initialize with custom service_id', () => {
      const serviceId = 'custom-service-id'
      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
        serviceId,
      })

      expect(service.serviceId).toBe(serviceId)
    })

    it('should initialize with model_id in arguments', () => {
      const service = new GoogleAIChatCompletion({
        geminiModelId: 'custom_model_id',
        apiKey: process.env.GOOGLE_AI_API_KEY,
      })

      expect(service.aiModelId).toBe('custom_model_id')
      expect(service.serviceId).toBe('custom_model_id')
    })

    it('should throw error when gemini_model_id is empty', () => {
      delete process.env.GOOGLE_AI_GEMINI_MODEL_ID

      expect(() => new GoogleAIChatCompletion()).toThrow(ServiceInitializationError)
      expect(() => new GoogleAIChatCompletion()).toThrow('The Google AI Gemini model ID is required.')
    })

    it('should throw error when api_key is empty and useVertexAI is false', () => {
      delete process.env.GOOGLE_AI_API_KEY

      expect(() => new GoogleAIChatCompletion({ geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID })).toThrow(
        ServiceInitializationError
      )
      expect(() => new GoogleAIChatCompletion({ geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID })).toThrow(
        'The API key is required when useVertexAI is false.'
      )
    })

    it('should throw error when useVertexAI is true but project_id is missing', () => {
      delete process.env.GOOGLE_AI_CLOUD_PROJECT_ID

      expect(
        () =>
          new GoogleAIChatCompletion({
            geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
            useVertexAI: true,
          })
      ).toThrow(ServiceInitializationError)
      expect(
        () =>
          new GoogleAIChatCompletion({
            geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
            useVertexAI: true,
          })
      ).toThrow('Project ID must be provided when useVertexAI is true.')
    })

    it('should return correct prompt execution settings class', () => {
      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
      })

      expect(service.getPromptExecutionSettingsClass()).toBe(GoogleAIChatPromptExecutionSettings)
    })
  })

  describe('getChatMessageContents', () => {
    it('should complete chat with basic settings', async () => {
      const mockResponse: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [{ text: 'Test content' }],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      const mockClient: any = {
        aio: {
          models: {
            // @ts-expect-error - Mock typing issue
            generate_content: jest.fn().mockResolvedValue(mockResponse),
            generate_content_stream: jest.fn(),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: 'test-model',
        apiKey: 'test-key',
        client: mockClient as any,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const settings = new GoogleAIChatPromptExecutionSettings({ topK: 5, temperature: 0.7 })

      const responses = await service.getChatMessageContents(chatHistory, settings)

      expect(mockClient.aio.models.generate_content).toHaveBeenCalledTimes(1)
      expect(responses).toHaveLength(1)
      expect(responses[0].role).toBe(AuthorRole.ASSISTANT)
      expect(responses[0].content).toBe('Test content')
      expect(responses[0].finishReason).toBe(FinishReason.STOP)
      expect(responses[0].metadata).toHaveProperty('usage')
      expect(responses[0].metadata).toHaveProperty('prompt_feedback')
    })

    it('should complete chat with custom client', async () => {
      const mockResponse: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [{ text: 'Test content' }],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      const mockClient: any = {
        aio: {
          models: {
            // @ts-expect-error - Mock typing issue
            generate_content: jest.fn().mockResolvedValue(mockResponse),
            generate_content_stream: jest.fn(),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: 'test-model',
        apiKey: 'test-key',
        client: mockClient as any,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const responses = await service.getChatMessageContents(chatHistory, new GoogleAIChatPromptExecutionSettings())

      expect(responses).toHaveLength(1)
      expect(responses[0].role).toBe(AuthorRole.ASSISTANT)
      expect(responses[0].content).toBe('Test content')
      expect(responses[0].finishReason).toBe(FinishReason.STOP)
      expect(mockClient.aio.models.generate_content).toHaveBeenCalledTimes(1)
    })

    it('should throw error when function choice behavior is set without kernel', async () => {
      const mockClient: any = {
        aio: {
          models: {
            // @ts-expect-error - Mock typing issue
            generate_content: jest.fn().mockResolvedValue({
              candidates: [
                {
                  content: {
                    parts: [{ text: 'Hello!' }],
                    role: 'model',
                  },
                  finish_reason: 'STOP',
                },
              ],
            }),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
        client: mockClient,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const settings = new GoogleAIChatPromptExecutionSettings()
      ;(settings as any).functionChoiceBehavior = FunctionChoiceBehavior.Auto()

      await expect(service.getChatMessageContents(chatHistory, settings)).rejects.toThrow(
        'The kernel is required for function calls.'
      )
    })

    it('should handle function choice behavior with tool calls', async () => {
      const mockResponseWithToolCall: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [
                {
                  functionCall: {
                    name: 'test_function',
                    args: { test_arg: 'test_value' },
                  },
                },
              ],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      const mockResponseFinal: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [{ text: 'Final response' }],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      const mockClient: any = {
        aio: {
          models: {
            generate_content:
              // @ts-expect-error - Mock typing issue
              jest.fn().mockResolvedValueOnce(mockResponseWithToolCall).mockResolvedValueOnce(mockResponseFinal),
            generate_content_stream: jest.fn(),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
        client: mockClient as any,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const kernel = new Kernel()
      jest.spyOn(kernel, 'getFullListOfFunctionMetadata').mockReturnValue([])
      const settings = new GoogleAIChatPromptExecutionSettings()
      ;(settings as any).functionChoiceBehavior = FunctionChoiceBehavior.Auto(true, undefined, {
        maximumAutoInvokeAttempts: 1,
      })

      const responses = await service.getChatMessageContents(chatHistory, settings, { kernel })

      // Should be called twice: once for tool call, once for final response
      expect(mockClient.aio.models.generate_content).toHaveBeenCalledTimes(2)
      expect(responses).toHaveLength(1)
      expect(responses[0].role).toBe(AuthorRole.ASSISTANT)
      expect(responses[0].finishReason).toBe(FinishReason.STOP)
    })

    it('should handle function choice behavior without tool call returned', async () => {
      const mockResponse: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [{ text: 'Test content' }],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      const mockClient: any = {
        aio: {
          models: {
            // @ts-expect-error - Mock typing issue
            generate_content: jest.fn().mockResolvedValue(mockResponse),
            generate_content_stream: jest.fn(),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
        client: mockClient as any,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const kernel = new Kernel()
      jest.spyOn(kernel, 'getFullListOfFunctionMetadata').mockReturnValue([])
      const settings = new GoogleAIChatPromptExecutionSettings()
      ;(settings as any).functionChoiceBehavior = FunctionChoiceBehavior.Auto(true, undefined, {
        maximumAutoInvokeAttempts: 1,
      })

      const responses = await service.getChatMessageContents(chatHistory, settings, { kernel })

      expect(mockClient.aio.models.generate_content).toHaveBeenCalledTimes(1)
      expect(responses).toHaveLength(1)
      expect(responses[0].role).toBe(AuthorRole.ASSISTANT)
      expect(responses[0].content).toBe('Test content')
    })
  })

  describe('getStreamingChatMessageContents', () => {
    it('should stream chat completion', async () => {
      const mockResponse: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [{ text: 'Test content' }],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      async function* mockStreamGenerator() {
        yield mockResponse
      }

      const mockClient: any = {
        aio: {
          models: {
            generate_content: jest.fn(),
            // @ts-expect-error - Mock typing issue
            generate_content_stream: jest.fn().mockResolvedValue(mockStreamGenerator()),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: 'test-model',
        apiKey: 'test-key',
        client: mockClient as any,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const settings = new GoogleAIChatPromptExecutionSettings()

      const chunks: any[] = []
      for await (const messages of service.getStreamingChatMessageContents(chatHistory, settings)) {
        chunks.push(messages)
        expect(messages).toHaveLength(1)
        expect(messages[0].role).toBe(AuthorRole.ASSISTANT)
        expect(messages[0].finishReason).toBe(FinishReason.STOP)
        expect(messages[0].metadata).toHaveProperty('usage')
        expect(messages[0].metadata).toHaveProperty('prompt_feedback')
      }

      expect(chunks.length).toBeGreaterThan(0)
      expect(mockClient.aio.models.generate_content_stream).toHaveBeenCalledTimes(1)
    })

    it('should stream chat completion with custom client', async () => {
      const mockResponse: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [{ text: 'Test content' }],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      async function* mockStreamGenerator() {
        yield mockResponse
      }

      const mockClient: any = {
        aio: {
          models: {
            generate_content: jest.fn(),
            generate_content_stream:
              // @ts-expect-error - Mock typing issue
              jest.fn().mockResolvedValue(mockStreamGenerator()),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: 'test-model',
        apiKey: 'test-key',
        client: mockClient as any,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const allMessages: any[] = []
      for await (const messages of service.getStreamingChatMessageContents(
        chatHistory,
        new GoogleAIChatPromptExecutionSettings()
      )) {
        allMessages.push(...messages)
        expect(messages).toHaveLength(1)
        expect(messages[0].role).toBe(AuthorRole.ASSISTANT)
        expect(messages[0].finishReason).toBe(FinishReason.STOP)
      }

      expect(allMessages.length).toBeGreaterThan(0)
      expect(mockClient.aio.models.generate_content_stream).toHaveBeenCalledTimes(1)
    })

    it('should throw error when streaming with function choice behavior without kernel', async () => {
      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const settings = new GoogleAIChatPromptExecutionSettings()
      ;(settings as any).functionChoiceBehavior = FunctionChoiceBehavior.Auto()

      const iterator = service.getStreamingChatMessageContents(chatHistory, settings)

      await expect(iterator.next()).rejects.toThrow('The kernel is required for function calls.')
    })

    it('should handle streaming with function choice behavior without tool call', async () => {
      const mockResponse: GenerateContentResponse = {
        candidates: [
          {
            index: 0,
            content: {
              role: 'user',
              parts: [{ text: 'Test content' }],
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
        },
      }

      async function* mockStreamGenerator() {
        yield mockResponse
      }

      const mockClient: any = {
        aio: {
          models: {
            generate_content: jest.fn(),
            generate_content_stream:
              // @ts-expect-error - Mock typing issue
              jest.fn().mockResolvedValue(mockStreamGenerator()),
          },
        },
      }

      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
        client: mockClient as any,
      })
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('Test message')

      const kernel = new Kernel()
      jest.spyOn(kernel, 'getFullListOfFunctionMetadata').mockReturnValue([])
      const settings = new GoogleAIChatPromptExecutionSettings()
      ;(settings as any).functionChoiceBehavior = FunctionChoiceBehavior.Auto(true, undefined, {
        maximumAutoInvokeAttempts: 1,
      })

      for await (const messages of service.getStreamingChatMessageContents(chatHistory, settings, { kernel })) {
        expect(messages).toHaveLength(1)
        expect(messages[0].role).toBe(AuthorRole.ASSISTANT)
        expect(messages[0].content).toBe('Test content')
      }

      expect(mockClient.aio.models.generate_content_stream).toHaveBeenCalledTimes(1)
    })
  })

  describe('_prepareChatHistoryForRequest', () => {
    it('should parse chat history correctly', () => {
      const service = new GoogleAIChatCompletion({
        geminiModelId: process.env.GOOGLE_AI_GEMINI_MODEL_ID,
        apiKey: process.env.GOOGLE_AI_API_KEY,
      })
      const chatHistory = new ChatHistory()

      chatHistory.addSystemMessage('test_system_message')
      chatHistory.addUserMessage('test_user_message')
      chatHistory.addAssistantMessage('test_assistant_message')

      const parsedChatHistory = (service as any)._prepareChatHistoryForRequest(chatHistory)

      expect(Array.isArray(parsedChatHistory)).toBe(true)
      // System message should be ignored (handled separately)
      expect(parsedChatHistory).toHaveLength(2)
      expect(parsedChatHistory[0].role).toBe('user')
      expect(parsedChatHistory[0].parts[0].text).toBe('test_user_message')
      expect(parsedChatHistory[1].role).toBe('model')
      expect(parsedChatHistory[1].parts[0].text).toBe('test_assistant_message')
    })
  })
})
