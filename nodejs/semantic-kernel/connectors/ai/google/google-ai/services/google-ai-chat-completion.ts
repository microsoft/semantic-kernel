import { GoogleGenerativeAI } from '@google/generative-ai'
import { ChatHistory } from '../../../../../contents/chat-history'
import { ChatMessageContent } from '../../../../../contents/chat-message-content'
import { FunctionCallContent } from '../../../../../contents/function-call-content'
import { StreamingChatMessageContent } from '../../../../../contents/streaming-chat-message-content'
import { StreamingTextContent } from '../../../../../contents/streaming-text-content'
import { TextContent } from '../../../../../contents/text-content'
import { AuthorRole } from '../../../../../contents/utils/author-role'
import { FinishReason } from '../../../../../contents/utils/finish-reason'
import {
  ServiceInitializationError,
  ServiceInvalidExecutionSettingsError,
} from '../../../../../exceptions/service-exceptions'
import { PromptExecutionSettings } from '../../../../../services/ai-service-client-base'
import { ChatCompletionClientBase } from '../../../chat-completion-client-base'
import { CompletionUsage } from '../../../completion-usage'
import { FunctionCallChoiceConfiguration } from '../../../function-call-choice-configuration'
import { FunctionChoiceType } from '../../../function-choice-type'
import {
  collapseFunctionCallResultsInChatHistory,
  filterSystemMessage,
  formatGeminiFunctionNameToKernelFunctionFullyQualifiedName,
} from '../../shared-utils'
import { GoogleAIChatPromptExecutionSettings } from '../google-ai-prompt-execution-settings'
import { GoogleAISettings } from '../google-ai-settings'
import {
  finishReasonFromGoogleAIToSemanticKernel,
  formatAssistantMessage,
  formatToolMessage,
  formatUserMessage,
  Part,
  updateSettingsFromFunctionChoiceConfiguration,
} from './utils'

// Google AI SDK types
interface GenerateContentResponse {
  candidates: Candidate[]
  prompt_feedback?: any
  usage_metadata?: {
    prompt_token_count?: number
    candidates_token_count?: number
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

interface Content {
  role: string
  parts: Part[]
}

interface GenerateContentConfig {
  system_instruction?: string
  [key: string]: any
}

interface GoogleClient {
  aio: {
    models: {
      generate_content(params: {
        model: string
        contents: Content[]
        config: GenerateContentConfig
      }): Promise<GenerateContentResponse>

      generate_content_stream(params: {
        model: string
        contents: Content[]
        config: GenerateContentConfig
      }): Promise<AsyncIterable<GenerateContentResponse>>
    }
  }
}

/**
 * Google AI Chat Completion Client.
 * Provides chat completion capabilities using Google's Gemini models.
 */
export class GoogleAIChatCompletion extends ChatCompletionClientBase {
  static readonly MODEL_PROVIDER_NAME = 'googleai'
  static readonly SUPPORTS_FUNCTION_CALLING = true

  // Properties from GoogleAIBase pattern
  serviceSettings: GoogleAISettings
  client: any | null = null

  /**
   * Initialize the Google AI Chat Completion Client.
   *
   * If no arguments are provided, the service will attempt to load the settings from the environment.
   * The following environment variables are used:
   * - GOOGLE_AI_GEMINI_MODEL_ID
   * - GOOGLE_AI_API_KEY
   * - GOOGLE_AI_CLOUD_PROJECT_ID
   * - GOOGLE_AI_CLOUD_REGION
   * - GOOGLE_AI_USE_VERTEXAI
   *
   * @param params - Configuration parameters
   * @param params.geminiModelId - The Gemini model ID (Optional)
   * @param params.apiKey - The API key (Optional)
   * @param params.projectId - The Google Cloud project ID (Optional)
   * @param params.region - The Google Cloud region (Optional)
   * @param params.useVertexAI - Whether to use Vertex AI (Optional)
   * @param params.serviceId - The service ID (Optional)
   * @param params.client - The Google AI Client to use (Optional)
   * @throws {ServiceInitializationError} If validation fails or required settings are missing
   */
  constructor(
    params: {
      geminiModelId?: string | null
      apiKey?: string | null
      projectId?: string | null
      region?: string | null
      useVertexAI?: boolean | null
      serviceId?: string | null
      client?: GoogleClient | null
    } = {}
  ) {
    let googleAISettings: GoogleAISettings

    try {
      googleAISettings = new GoogleAISettings({
        geminiModelId: params.geminiModelId ?? undefined,
        apiKey: params.apiKey ?? undefined,
        cloudProjectId: params.projectId ?? undefined,
        cloudRegion: params.region ?? undefined,
        useVertexAI: params.useVertexAI ?? undefined,
      })
    } catch (error) {
      throw new ServiceInitializationError(
        `Failed to validate Google AI settings: ${error instanceof Error ? error.message : String(error)}`
      )
    }

    if (!googleAISettings.geminiModelId) {
      throw new ServiceInitializationError('The Google AI Gemini model ID is required.')
    }

    if (!params.client) {
      if (googleAISettings.useVertexAI && !googleAISettings.cloudProjectId) {
        throw new ServiceInitializationError('Project ID must be provided when useVertexAI is true.')
      }
      if (!googleAISettings.useVertexAI && !googleAISettings.apiKey) {
        throw new ServiceInitializationError('The API key is required when useVertexAI is false.')
      }
    }

    // Call parent constructor with aiModelId and serviceId
    super({
      aiModelId: googleAISettings.geminiModelId!,
      serviceId: params.serviceId || googleAISettings.geminiModelId,
    })

    // Initialize GoogleAI-specific properties
    this.serviceSettings = googleAISettings
    this.client = params.client ?? null
  }

  /**
   * Get the prompt execution settings class for this service.
   * @override
   */
  getPromptExecutionSettingsClass(): typeof GoogleAIChatPromptExecutionSettings {
    return GoogleAIChatPromptExecutionSettings
  }

  /**
   * Internal implementation for getting chat message contents.
   * This method is called by the base class's getChatMessageContents() method.
   *
   * @param chatHistory - The chat history to send
   * @param settings - Execution settings for the request
   * @returns Array of chat message content responses
   * @protected
   * @override
   */
  protected async _innerGetChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings
  ): Promise<ChatMessageContent[]> {
    let executionSettings: GoogleAIChatPromptExecutionSettings

    if (!(settings instanceof GoogleAIChatPromptExecutionSettings)) {
      executionSettings = this.getPromptExecutionSettingsFromSettings(settings)
    } else {
      executionSettings = settings
    }
    // Type assertion for safety (matches Python implementation)
    if (!(executionSettings instanceof GoogleAIChatPromptExecutionSettings)) {
      throw new ServiceInitializationError('Failed to convert settings to GoogleAIChatPromptExecutionSettings')
    }

    if (!this.serviceSettings.geminiModelId) {
      throw new ServiceInitializationError('The Google AI Gemini model ID is required.')
    }

    collapseFunctionCallResultsInChatHistory(chatHistory)

    const generateContent = async (client: GoogleClient): Promise<GenerateContentResponse> => {
      return await client.aio.models.generate_content({
        model: this.serviceSettings.geminiModelId!,
        contents: this._prepareChatHistoryForRequest(chatHistory),
        config: {
          system_instruction: filterSystemMessage(chatHistory) ?? undefined,
          ...executionSettings.prepareSettingsDict(),
        },
      })
    }

    let response: GenerateContentResponse

    if (this.client) {
      response = await generateContent(this.client)
    } else if (this.serviceSettings.useVertexAI) {
      const client = this.createVertexAIClient()
      try {
        response = await generateContent(client)
      } finally {
        this.closeClient(client)
      }
    } else {
      const client = this.createAPIClient()
      try {
        response = await generateContent(client)
      } finally {
        this.closeClient(client)
      }
    }

    return response.candidates.map((candidate) => this._createChatMessageContent(response, candidate))
  }

  /**
   * Internal implementation for getting streaming chat message contents.
   * This method is called by the base class's getStreamingChatMessageContents() method.
   *
   * @param chatHistory - The chat history to send
   * @param settings - Execution settings for the request
   * @param functionInvokeAttempt - The function invoke attempt counter
   * @returns Async generator yielding arrays of streaming chat message content
   * @protected
   * @override
   */
  protected async *_innerGetStreamingChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings,
    functionInvokeAttempt: number = 0
  ): AsyncGenerator<StreamingChatMessageContent[], void> {
    let executionSettings: GoogleAIChatPromptExecutionSettings

    if (!(settings instanceof GoogleAIChatPromptExecutionSettings)) {
      executionSettings = this.getPromptExecutionSettingsFromSettings(settings)
    } else {
      executionSettings = settings
    }
    // Type assertion for safety (matches Python implementation)
    if (!(executionSettings instanceof GoogleAIChatPromptExecutionSettings)) {
      throw new ServiceInitializationError('Failed to convert settings to GoogleAIChatPromptExecutionSettings')
    }

    if (!this.serviceSettings.geminiModelId) {
      throw new ServiceInitializationError('The Google AI Gemini model ID is required.')
    }

    collapseFunctionCallResultsInChatHistory(chatHistory)

    const generateContentStream = async function* (
      this: GoogleAIChatCompletion,
      client: GoogleClient
    ): AsyncGenerator<GenerateContentResponse, void> {
      const stream = await client.aio.models.generate_content_stream({
        model: this.serviceSettings.geminiModelId!,
        contents: this._prepareChatHistoryForRequest(chatHistory),
        config: {
          system_instruction: filterSystemMessage(chatHistory) ?? undefined,
          ...executionSettings.prepareSettingsDict(),
        },
      })

      for await (const chunk of stream) {
        yield chunk
      }
    }.bind(this)

    if (this.client) {
      for await (const chunk of generateContentStream(this.client)) {
        yield chunk.candidates.map((candidate) =>
          this._createStreamingChatMessageContent(chunk, candidate, functionInvokeAttempt)
        )
      }
    } else if (this.serviceSettings.useVertexAI) {
      const client = this.createVertexAIClient()
      try {
        for await (const chunk of generateContentStream(client)) {
          yield chunk.candidates.map((candidate) =>
            this._createStreamingChatMessageContent(chunk, candidate, functionInvokeAttempt)
          )
        }
      } finally {
        this.closeClient(client)
      }
    } else {
      const client = this.createAPIClient()
      try {
        for await (const chunk of generateContentStream(client)) {
          yield chunk.candidates.map((candidate) =>
            this._createStreamingChatMessageContent(chunk, candidate, functionInvokeAttempt)
          )
        }
      } finally {
        this.closeClient(client)
      }
    }
  }

  /**
   * Verify function choice settings are valid.
   *
   * @param settings - The settings to verify
   * @protected
   * @override
   */
  protected _verifyFunctionChoiceSettings(settings: PromptExecutionSettings): void {
    if (!(settings instanceof GoogleAIChatPromptExecutionSettings)) {
      throw new ServiceInvalidExecutionSettingsError('The settings must be a GoogleAIChatPromptExecutionSettings.')
    }
    if (settings.candidateCount !== null && settings.candidateCount !== undefined && settings.candidateCount > 1) {
      throw new ServiceInvalidExecutionSettingsError(
        'Auto-invocation of tool calls may only be used with a GoogleAIChatPromptExecutionSettings.candidateCount of 1.'
      )
    }
  }

  /**
   * Get the callback for updating function choice settings.
   *
   * @returns The callback function
   * @protected
   * @override
   */
  protected _updateFunctionChoiceSettingsCallback(): (
    configuration: FunctionCallChoiceConfiguration,
    settings: PromptExecutionSettings,
    choiceType: FunctionChoiceType
  ) => void {
    return (
      configuration: FunctionCallChoiceConfiguration,
      settings: PromptExecutionSettings,
      choiceType: FunctionChoiceType
    ) => {
      updateSettingsFromFunctionChoiceConfiguration(configuration, settings, choiceType)
    }
  }

  /**
   * Reset function choice settings.
   *
   * @param settings - The settings to reset
   * @protected
   * @override
   */
  protected _resetFunctionChoiceSettings(settings: PromptExecutionSettings): void {
    if ('toolConfig' in settings) {
      ;(settings as any).toolConfig = null
    }
    if ('tools' in settings) {
      ;(settings as any).tools = null
    }
  }

  /**
   * Prepare chat history for request.
   *
   * @param chatHistory - The chat history to prepare
   * @param roleKey - The role key (unused, for compatibility)
   * @param contentKey - The content key (unused, for compatibility)
   * @returns The prepared chat history
   * @protected
   * @override
   */
  protected _prepareChatHistoryForRequest(
    chatHistory: ChatHistory,
    _roleKey: string = 'role',
    _contentKey: string = 'content'
  ): Content[] {
    const chatRequestMessages: Content[] = []

    for (const message of chatHistory.messages) {
      if (message.role === AuthorRole.SYSTEM) {
        // Skip system messages since they are not part of the chat request.
        // System message will be provided as system_instruction in the config.
        continue
      }
      if (message.role === AuthorRole.USER) {
        chatRequestMessages.push({ role: 'user', parts: formatUserMessage(message) })
      } else if (message.role === AuthorRole.ASSISTANT) {
        chatRequestMessages.push({ role: 'model', parts: formatAssistantMessage(message) })
      } else if (message.role === AuthorRole.TOOL) {
        chatRequestMessages.push({ role: 'function', parts: formatToolMessage(message) })
      }
    }

    return chatRequestMessages
  }

  // #region Helper methods

  /**
   * Create a chat message content object from a response and candidate.
   *
   * @param response - The response from the service
   * @param candidate - The candidate from the response
   * @returns A chat message content object
   * @private
   */
  private _createChatMessageContent(response: GenerateContentResponse, candidate: Candidate): ChatMessageContent {
    // Best effort conversion of finish reason. The raw value will be available in metadata.
    const finishReason: FinishReason | null = finishReasonFromGoogleAIToSemanticKernel(candidate.finish_reason)
    const responseMetadata = {
      ...this._getMetadataFromResponse(response),
      ...this._getMetadataFromCandidate(candidate),
    }

    const items: Array<TextContent | FunctionCallContent> = []

    if (candidate.content && candidate.content.parts) {
      for (let idx = 0; idx < candidate.content.parts.length; idx++) {
        const part = candidate.content.parts[idx]
        if (part.text) {
          items.push(
            new TextContent({
              text: part.text,
              innerContent: response,
              metadata: responseMetadata,
            })
          )
        } else if (part.functionCall) {
          items.push(
            new FunctionCallContent({
              id: `${part.functionCall.name}_${idx}`,
              name: formatGeminiFunctionNameToKernelFunctionFullyQualifiedName(part.functionCall.name),
              arguments: { ...part.functionCall.args },
            })
          )
        }
      }
    }

    return new ChatMessageContent({
      aiModelId: this.aiModelId,
      role: AuthorRole.ASSISTANT,
      items,
      innerContent: response,
      finishReason: finishReason ?? undefined,
      metadata: responseMetadata,
    })
  }

  /**
   * Create a streaming chat message content object from a chunk and candidate.
   *
   * @param chunk - The response chunk from the service
   * @param candidate - The candidate from the chunk
   * @param functionInvokeAttempt - The function invoke attempt counter
   * @returns A streaming chat message content object
   * @private
   */
  private _createStreamingChatMessageContent(
    chunk: GenerateContentResponse,
    candidate: Candidate,
    functionInvokeAttempt: number = 0
  ): StreamingChatMessageContent {
    // Best effort conversion of finish reason. The raw value will be available in metadata.
    const finishReason: FinishReason | null = finishReasonFromGoogleAIToSemanticKernel(candidate.finish_reason)
    const responseMetadata = {
      ...this._getMetadataFromResponse(chunk),
      ...this._getMetadataFromCandidate(candidate),
    }

    const items: Array<StreamingTextContent | FunctionCallContent> = []

    if (candidate.content && candidate.content.parts) {
      for (let idx = 0; idx < candidate.content.parts.length; idx++) {
        const part = candidate.content.parts[idx]
        if (part.text) {
          items.push(
            new StreamingTextContent({
              choiceIndex: candidate.index ?? 0,
              text: part.text,
              innerContent: chunk,
              metadata: responseMetadata,
            })
          )
        } else if (part.functionCall) {
          items.push(
            new FunctionCallContent({
              id: `${part.functionCall.name}_${idx}`,
              name: formatGeminiFunctionNameToKernelFunctionFullyQualifiedName(part.functionCall.name),
              arguments: { ...part.functionCall.args },
            })
          )
        }
      }
    }

    return new StreamingChatMessageContent({
      aiModelId: this.aiModelId,
      role: AuthorRole.ASSISTANT,
      choiceIndex: candidate.index ?? 0,
      items,
      innerContent: chunk,
      finishReason: finishReason ?? undefined,
      metadata: responseMetadata,
      functionInvokeAttempt,
    })
  }

  /**
   * Extract metadata from a response object.
   *
   * @param response - The response from the service
   * @returns A dictionary containing metadata
   * @private
   */
  private _getMetadataFromResponse(response: GenerateContentResponse): Record<string, any> {
    return {
      prompt_feedback: response.prompt_feedback,
      usage: new CompletionUsage({
        promptTokens: response.usage_metadata ? (response.usage_metadata.prompt_token_count ?? undefined) : undefined,
        completionTokens: response.usage_metadata
          ? (response.usage_metadata.candidates_token_count ?? undefined)
          : undefined,
      }),
    }
  }

  /**
   * Extract metadata from a candidate object.
   *
   * @param candidate - The candidate from the response
   * @returns A dictionary containing metadata
   * @private
   */
  private _getMetadataFromCandidate(candidate: Candidate): Record<string, any> {
    return {
      index: candidate.index,
      finish_reason: candidate.finish_reason,
      safety_ratings: candidate.safety_ratings,
      token_count: candidate.token_count,
    }
  }

  /**
   * Helper method to create a Vertex AI client.
   * Implements the client creation pattern from GoogleAIBase.
   *
   * Creates a client using Vertex AI with the configured project ID and region.
   * Equivalent to Python's: Client(vertexai=True, project=..., location=...)
   *
   * @private
   */
  private createVertexAIClient(): GoogleClient {
    // This would use the Google GenAI SDK's Client class:
    // const { Client } = require('@google/generative-ai') or similar
    // return new Client({
    //   vertexai: true,
    //   project: this.serviceSettings.cloudProjectId,
    //   location: this.serviceSettings.cloudRegion,
    // })
    throw new Error(
      'Vertex AI client creation requires the Google GenAI SDK. ' +
        'Install the package and implement client creation using: ' +
        'new Client({ vertexai: true, project: cloudProjectId, location: cloudRegion })'
    )
  }

  /**
   * Helper method to create an API key-based client.
   * Implements the client creation pattern from GoogleAIBase.
   *
   * Creates a client using an API key for authentication.
   * Equivalent to Python's: Client(api_key=api_key)
   *
   * @private
   */
  private createAPIClient(): GoogleClient {
    if (!this.serviceSettings.apiKey) {
      throw new ServiceInitializationError('API key is required to create a client.')
    }

    const genAI = new GoogleGenerativeAI(this.serviceSettings.apiKey)
    const model = genAI.getGenerativeModel({ model: this.serviceSettings.geminiModelId! })

    // Wrap the Google Generative AI client to match our GoogleClient interface
    return {
      aio: {
        models: {
          generate_content: async (params: {
            model: string
            contents: Content[]
            config: GenerateContentConfig
          }): Promise<GenerateContentResponse> => {
            const result = await model.generateContent({
              contents: params.contents,
              systemInstruction: params.config.system_instruction,
              generationConfig: params.config,
            } as any)
            const response = result.response
            return {
              candidates:
                response.candidates?.map((candidate) => ({
                  index: candidate.index,
                  content: candidate.content,
                  finish_reason: candidate.finishReason,
                  safety_ratings: candidate.safetyRatings,
                })) || [],
              prompt_feedback: response.promptFeedback,
              usage_metadata: {
                prompt_token_count: response.usageMetadata?.promptTokenCount,
                candidates_token_count: response.usageMetadata?.candidatesTokenCount,
              },
            }
          },
          generate_content_stream: async (params: {
            model: string
            contents: Content[]
            config: GenerateContentConfig
          }): Promise<AsyncIterable<GenerateContentResponse>> => {
            const result = await model.generateContentStream({
              contents: params.contents,
              systemInstruction: params.config.system_instruction,
              generationConfig: params.config,
            } as any)

            async function* streamWrapper(): AsyncGenerator<GenerateContentResponse, void> {
              for await (const chunk of result.stream) {
                yield {
                  candidates:
                    chunk.candidates?.map((candidate) => ({
                      index: candidate.index,
                      content: candidate.content,
                      finish_reason: candidate.finishReason,
                      safety_ratings: candidate.safetyRatings,
                    })) || [],
                  prompt_feedback: chunk.promptFeedback,
                  usage_metadata: {
                    prompt_token_count: chunk.usageMetadata?.promptTokenCount,
                    candidates_token_count: chunk.usageMetadata?.candidatesTokenCount,
                  },
                }
              }
            }

            return streamWrapper()
          },
        },
      },
    }
  }

  /**
   * Helper method to close/cleanup a client.
   *
   * @param _client - The client to clean up
   * @private
   */
  private closeClient(_client: GoogleClient): void {
    // Implement cleanup if needed
    // Python uses context managers (with statement), TypeScript might need explicit cleanup
  }

  /**
   * Convert generic settings to Google AI specific settings.
   * Overrides the base class method to provide Google AI specific conversion.
   *
   * @param settings - Generic prompt execution settings
   * @returns Google AI specific settings
   * @override
   */
  getPromptExecutionSettingsFromSettings(settings: PromptExecutionSettings): GoogleAIChatPromptExecutionSettings {
    // Convert or validate settings to Google AI specific format
    if (settings instanceof GoogleAIChatPromptExecutionSettings) {
      return settings
    }

    // Create new Google AI settings from generic settings
    return new GoogleAIChatPromptExecutionSettings()
  }

  // #endregion
}
