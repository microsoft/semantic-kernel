import OpenAI from 'openai'
import type { Stream } from 'openai/streaming'
import { AnnotationContent } from '../../../../contents/annotation-content'
import { ChatHistory } from '../../../../contents/chat-history'
import { ChatMessageContent } from '../../../../contents/chat-message-content'
import { FileReferenceContent } from '../../../../contents/file-reference-content'
import { FunctionCallContent } from '../../../../contents/function-call-content'
import { StreamingChatMessageContent } from '../../../../contents/streaming-chat-message-content'
import { StreamingTextContent } from '../../../../contents/streaming-text-content'
import { TextContent } from '../../../../contents/text-content'
import { AuthorRole } from '../../../../contents/utils/author-role'
import { FinishReason } from '../../../../contents/utils/finish-reason'
import { AutoFunctionInvocationContext } from '../../../../filters/auto-function-invocation/auto-function-invocation-context'
import { KernelArguments } from '../../../../functions/kernel-arguments'
import { Kernel } from '../../../../kernel'
import { KernelJsonSchemaBuilder } from '../../../../schema/kernel-json-schema-builder'
import { PromptExecutionSettings } from '../../../../services/ai-service-client-base'
import { createDefaultLogger } from '../../../../utils/logger'
import { generateStructuredOutputResponseFormatSchema } from '../../../utils/structured-output-schema'
import { ChatCompletionClientBase } from '../../chat-completion-client-base'
import { CompletionUsage } from '../../completion-usage'
import { FunctionCallChoiceConfiguration } from '../../function-call-choice-configuration'
import { updateSettingsFromFunctionCallConfiguration } from '../../function-calling-utils'
import { FunctionChoiceBehavior } from '../../function-choice-behavior'
import { FunctionChoiceType } from '../../function-choice-type'
import { OpenAIChatPromptExecutionSettings } from '../prompt-execution-settings/open-ai-prompt-execution-settings'
import { OpenAIModelTypes } from './open-ai-model-types'

const logger = createDefaultLogger('OpenAIChatCompletionBase')

/**
 * OpenAI chat completion base class.
 */
export abstract class OpenAIChatCompletionBase extends ChatCompletionClientBase {
  // Properties from OpenAIHandler
  client: OpenAI
  aiModelType: OpenAIModelTypes = OpenAIModelTypes.CHAT
  promptTokens: number = 0
  completionTokens: number = 0
  totalTokens: number = 0

  static readonly MODEL_PROVIDER_NAME = 'openai'
  static readonly SUPPORTS_FUNCTION_CALLING = true

  // Note: aiModelId and serviceId are inherited from AIServiceClientBase
  instructionRole: string = 'system'

  /**
   * Constructor for OpenAIChatCompletionBase.
   * @param client - The OpenAI client instance
   * @param aiModelId - The AI model ID
   * @param serviceId - The service ID (optional, defaults to aiModelId)
   * @param aiModelType - The AI model type (default: CHAT)
   */
  constructor(
    client: OpenAI,
    aiModelId: string,
    serviceId?: string,
    aiModelType: OpenAIModelTypes = OpenAIModelTypes.CHAT
  ) {
    super({ aiModelId, serviceId })
    this.client = client
    this.aiModelType = aiModelType
  }

  // #region Methods from OpenAIHandler

  /**
   * Send a request to the OpenAI API.
   *
   * @param settings - The prompt execution settings
   * @returns The response from the OpenAI API
   */
  protected async sendRequest(settings: PromptExecutionSettings): Promise<any> {
    if (this.aiModelType === OpenAIModelTypes.TEXT || this.aiModelType === OpenAIModelTypes.CHAT) {
      return await this.sendCompletionRequest(settings as any)
    }

    throw new Error(`Model type ${this.aiModelType} is not supported`)
  }

  /**
   * Execute the appropriate call to OpenAI models.
   *
   * @param settings - The prompt execution settings
   * @returns The completion response
   */
  protected async sendCompletionRequest(
    settings: any
  ): Promise<
    | OpenAI.Chat.ChatCompletion
    | OpenAI.Completion
    | Stream<OpenAI.Chat.Completions.ChatCompletionChunk>
    | Stream<OpenAI.Completions.Completion>
  > {
    try {
      const settingsDict = settings.prepareSettingsDict()

      // Ensure the model parameter is set
      if (!settingsDict.model) {
        settingsDict.model = this.aiModelId
      }

      if (this.aiModelType === OpenAIModelTypes.CHAT) {
        const chatSettings = settings as any
        this.handleStructuredOutput(chatSettings, settingsDict)

        if (chatSettings.tools === null || chatSettings.tools === undefined) {
          delete settingsDict.parallelToolCalls
        }

        const response = await this.client.chat.completions.create(settingsDict as any)
        this.storeUsage(response)
        return response
      } else {
        const response = await this.client.completions.create(settingsDict as any)
        this.storeUsage(response)
        return response
      }
    } catch (error: any) {
      if (error.code === 'content_filter') {
        throw new Error(`${this.constructor.name} service encountered a content error: ${error.message}`, {
          cause: error,
        })
      }
      throw new Error(`${this.constructor.name} service failed to complete the prompt: ${error.message}`, {
        cause: error,
      })
    }
  }

  /**
   * Handle structured output for chat completions.
   *
   * @param requestSettings - The chat prompt execution settings
   * @param settings - The settings dictionary to modify
   */
  protected handleStructuredOutput(requestSettings: any, settings: Record<string, any>): void {
    const responseFormat = requestSettings.responseFormat

    if (requestSettings.structuredJsonResponse && responseFormat) {
      // Case 1: response_format is a class/constructor with a schema
      if (typeof responseFormat === 'function' && this.hasSchema(responseFormat)) {
        // For classes with schemas (e.g., Zod schemas)
        settings.responseFormat = responseFormat
      }
      // Case 2: response_format is a type/class without built-in schema
      else if (typeof responseFormat === 'function') {
        const generatedSchema = KernelJsonSchemaBuilder.build(responseFormat, {
          structuredOutput: true,
        })

        if (generatedSchema) {
          settings.responseFormat = generateStructuredOutputResponseFormatSchema(responseFormat.name, generatedSchema)
        }
      }
      // Case 3: response_format is a dictionary, pass it without modification
      else if (typeof responseFormat === 'object' && responseFormat !== null) {
        settings.responseFormat = responseFormat
      }
    }
  }

  /**
   * Store the usage information from the response.
   *
   * @param response - The response from the OpenAI API
   */
  protected storeUsage(response: any): void {
    // Handle image responses
    if (response && 'created' in response && 'data' in response && response.usage) {
      // This is likely an ImagesResponse
      logger.info(`OpenAI image usage: ${JSON.stringify(response.usage)}`)
      if (response.usage.input_tokens !== undefined) {
        this.promptTokens += response.usage.input_tokens
      }
      if (response.usage.total_tokens !== undefined) {
        this.totalTokens += response.usage.total_tokens
      }
      if (response.usage.output_tokens !== undefined) {
        this.completionTokens += response.usage.output_tokens
      }
      return
    }

    // Handle regular completion responses
    if (response && response.usage && !this.isStream(response)) {
      logger.info(`OpenAI usage: ${JSON.stringify(response.usage)}`)

      if (response.usage.prompt_tokens !== undefined) {
        this.promptTokens += response.usage.prompt_tokens
      }
      if (response.usage.total_tokens !== undefined) {
        this.totalTokens += response.usage.total_tokens
      }
      if (response.usage.completion_tokens !== undefined) {
        this.completionTokens += response.usage.completion_tokens
      }
    }
  }

  /**
   * Check if a value is a stream.
   *
   * @private
   */
  private isStream(value: any): boolean {
    return (
      value &&
      typeof value === 'object' &&
      (typeof value[Symbol.asyncIterator] === 'function' || typeof value.getReader === 'function')
    )
  }

  /**
   * Check if a type has a schema method or property.
   *
   * @private
   */
  private hasSchema(value: any): boolean {
    return typeof value === 'function' && (value.schema !== undefined || value.prototype?.schema !== undefined)
  }

  // #endregion

  // #region Overriding base class methods

  /**
   * Get the prompt execution settings class.
   */
  getPromptExecutionSettingsClass(): any {
    return OpenAIChatPromptExecutionSettings
  }

  /**
   * Get prompt execution settings from generic settings.
   */
  getPromptExecutionSettingsFromSettings(settings: PromptExecutionSettings): OpenAIChatPromptExecutionSettings {
    if (settings instanceof OpenAIChatPromptExecutionSettings) {
      return settings
    }
    return new OpenAIChatPromptExecutionSettings(settings)
  }

  /**
   * Get the service URL.
   */
  serviceUrl(): string | null {
    return this.client.baseURL
  }

  /**
   * Internal method to get chat message contents.
   *
   * @param chatHistory - The chat history
   * @param settings - The prompt execution settings
   * @returns A promise resolving to an array of chat message contents
   */
  protected async _innerGetChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings
  ): Promise<ChatMessageContent[]> {
    if (!(settings instanceof OpenAIChatPromptExecutionSettings)) {
      settings = this.getPromptExecutionSettingsFromSettings(settings)
    }

    const openAISettings = settings as OpenAIChatPromptExecutionSettings
    openAISettings.stream = false
    ;(openAISettings as any).messages = this._prepareChatHistoryForRequest(chatHistory)
    openAISettings.aiModelId = openAISettings.aiModelId || this.aiModelId

    const response = await this.sendRequest(openAISettings)

    if (!this._isChatCompletion(response)) {
      throw new Error('Expected a ChatCompletion response.')
    }

    const responseMetadata = this._getMetadataFromChatResponse(response)
    return (response as any).choices.map((choice: any) =>
      this._createChatMessageContent(response, choice, responseMetadata)
    )
  }

  /**
   * Internal method to get streaming chat message contents.
   *
   * @param chatHistory - The chat history
   * @param settings - The prompt execution settings
   * @param functionInvokeAttempt - The function invocation attempt count
   * @returns An async generator yielding streaming chat message contents
   */
  protected async *_innerGetStreamingChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings,
    functionInvokeAttempt: number = 0
  ): AsyncGenerator<StreamingChatMessageContent[], void> {
    if (!(settings instanceof OpenAIChatPromptExecutionSettings)) {
      settings = this.getPromptExecutionSettingsFromSettings(settings)
    }

    const openAISettings = settings as OpenAIChatPromptExecutionSettings
    openAISettings.stream = true
    ;(openAISettings as any).streamOptions = { include_usage: true }
    ;(openAISettings as any).messages = this._prepareChatHistoryForRequest(chatHistory)
    openAISettings.aiModelId = openAISettings.aiModelId || this.aiModelId

    const response = await this.sendRequest(openAISettings)

    if (!this._isStream(response)) {
      throw new Error('Expected an AsyncStream[ChatCompletionChunk] response.')
    }

    for await (const chunk of response as any) {
      if (chunk.choices.length === 0 && !chunk.usage) {
        continue
      }

      const chunkMetadata = this._getMetadataFromStreamingChatResponse(chunk)

      if ((!chunk.choices || chunk.choices.length === 0) && chunk.usage) {
        // Usage is contained in the last chunk where the choices are empty
        // We are duplicating the usage metadata to all the choices in the response
        yield Array.from(
          { length: openAISettings.numberOfResponses || 1 },
          (_, i) =>
            new StreamingChatMessageContent({
              role: AuthorRole.ASSISTANT,
              content: '',
              choiceIndex: i,
              innerContent: chunk,
              aiModelId: openAISettings.aiModelId,
              metadata: chunkMetadata,
              functionInvokeAttempt,
            })
        )
      } else {
        yield chunk.choices.map((choice: any) =>
          this._createStreamingChatMessageContent(chunk, choice, chunkMetadata, functionInvokeAttempt)
        )
      }
    }
  }

  /**
   * Verify function choice settings.
   *
   * @param settings - The prompt execution settings to verify
   */
  protected _verifyFunctionChoiceSettings(settings: PromptExecutionSettings): void {
    if (!(settings instanceof OpenAIChatPromptExecutionSettings)) {
      throw new Error('The settings must be an OpenAIChatPromptExecutionSettings.')
    }

    if (settings.numberOfResponses && settings.numberOfResponses > 1) {
      throw new Error(
        'Auto-invocation of tool calls may only be used with a ' + 'OpenAIChatPromptExecutions.numberOfResponses of 1.'
      )
    }
  }

  /**
   * Get the update function choice settings callback.
   */
  protected _updateFunctionChoiceSettingsCallback(): (
    config: FunctionCallChoiceConfiguration,
    settings: PromptExecutionSettings,
    choiceType: FunctionChoiceType
  ) => void {
    return updateSettingsFromFunctionCallConfiguration
  }

  /**
   * Reset function choice settings.
   *
   * @param settings - The prompt execution settings to reset
   */
  protected _resetFunctionChoiceSettings(settings: PromptExecutionSettings): void {
    const anySettings = settings as any
    if ('toolChoice' in anySettings) {
      anySettings.toolChoice = null
    }
    if ('tools' in anySettings) {
      anySettings.tools = null
    }
  }

  // #endregion

  // #region Content creation

  /**
   * Create a chat message content object from a choice.
   *
   * @param response - The chat completion response
   * @param choice - The choice to convert
   * @param responseMetadata - Response metadata
   * @returns A chat message content
   */
  protected _createChatMessageContent(
    response: any,
    choice: any,
    responseMetadata: Record<string, any>
  ): ChatMessageContent {
    const metadata = { ...this._getMetadataFromChatChoice(choice), ...responseMetadata }

    const items: any[] = [...this._getToolCallsFromChatChoice(choice), ...this._getFunctionCallFromChatChoice(choice)]

    if (choice.message.content) {
      items.push(new TextContent({ text: choice.message.content }))
    } else if ('refusal' in choice.message && choice.message.refusal) {
      items.push(new TextContent({ text: choice.message.refusal }))
    }

    return new ChatMessageContent({
      innerContent: response,
      aiModelId: this.aiModelId,
      metadata,
      role: AuthorRole[choice.message.role.toUpperCase() as keyof typeof AuthorRole] || AuthorRole.ASSISTANT,
      items,
      finishReason: choice.finish_reason
        ? FinishReason[choice.finish_reason.toUpperCase() as keyof typeof FinishReason]
        : undefined,
    })
  }

  /**
   * Create a streaming chat message content object from a choice.
   *
   * @param chunk - The chat completion chunk
   * @param choice - The choice to convert
   * @param chunkMetadata - Chunk metadata
   * @param functionInvokeAttempt - The function invocation attempt count
   * @returns A streaming chat message content
   */
  protected _createStreamingChatMessageContent(
    chunk: any,
    choice: any,
    chunkMetadata: Record<string, any>,
    functionInvokeAttempt: number
  ): StreamingChatMessageContent {
    const metadata = { ...this._getMetadataFromChatChoice(choice), ...chunkMetadata }

    const items: any[] = [...this._getToolCallsFromChatChoice(choice), ...this._getFunctionCallFromChatChoice(choice)]

    if (choice.delta?.content) {
      items.push(
        new StreamingTextContent({
          choiceIndex: choice.index,
          text: choice.delta.content,
        })
      )
    }

    return new StreamingChatMessageContent({
      choiceIndex: choice.index,
      innerContent: chunk,
      aiModelId: this.aiModelId,
      metadata,
      role: choice.delta?.role
        ? AuthorRole[choice.delta.role.toUpperCase() as keyof typeof AuthorRole]
        : AuthorRole.ASSISTANT,
      finishReason: choice.finish_reason
        ? FinishReason[choice.finish_reason.toUpperCase() as keyof typeof FinishReason]
        : undefined,
      items,
      functionInvokeAttempt,
    })
  }

  /**
   * Get metadata from a chat response.
   *
   * @param response - The chat completion response
   * @returns Metadata object
   */
  protected _getMetadataFromChatResponse(response: any): Record<string, any> {
    return {
      id: response.id,
      created: response.created,
      systemFingerprint: response.system_fingerprint,
      usage: response.usage ? CompletionUsage.fromOpenAI(response.usage) : null,
    }
  }

  /**
   * Get metadata from a streaming chat response.
   *
   * @param response - The chat completion chunk
   * @returns Metadata object
   */
  protected _getMetadataFromStreamingChatResponse(response: any): Record<string, any> {
    return {
      id: response.id,
      created: response.created,
      systemFingerprint: response.system_fingerprint,
      usage: response.usage ? CompletionUsage.fromOpenAI(response.usage) : null,
    }
  }

  /**
   * Get metadata from a chat choice.
   *
   * @param choice - The choice
   * @returns Metadata object
   */
  protected _getMetadataFromChatChoice(choice: any): Record<string, any> {
    return {
      logprobs: (choice as any).logprobs || null,
    }
  }

  /**
   * Get tool calls from a chat choice.
   *
   * @param choice - The choice
   * @returns Array of function call contents
   */
  protected _getToolCallsFromChatChoice(choice: any): FunctionCallContent[] {
    const content = 'message' in choice ? choice.message : choice.delta

    if (content && 'tool_calls' in content && content.tool_calls) {
      return content.tool_calls
        .filter((tool: any) => tool.function)
        .map(
          (tool: any) =>
            new FunctionCallContent({
              id: tool.id,
              index: tool.index,
              name: tool.function.name,
              arguments: tool.function.arguments,
            })
        )
    }

    // When you enable asynchronous content filtering in Azure OpenAI, you may receive empty deltas
    return []
  }

  /**
   * Get function call from a chat choice (legacy).
   *
   * @param choice - The choice
   * @returns Array of function call contents
   */
  protected _getFunctionCallFromChatChoice(choice: any): FunctionCallContent[] {
    const content = 'message' in choice ? choice.message : choice.delta

    if (content && 'function_call' in content && content.function_call) {
      const functionCall = content.function_call
      return [
        new FunctionCallContent({
          id: 'legacy_function_call',
          name: functionCall.name || '',
          arguments: functionCall.arguments || '',
        }),
      ]
    }

    // When you enable asynchronous content filtering in Azure OpenAI, you may receive empty deltas
    return []
  }

  /**
   * Prepare the chat history for a request.
   *
   * Allowing customization of the key names for role/author, and optionally overriding the role.
   *
   * ChatRole.TOOL messages need to be formatted different than system/user/assistant messages:
   * They require a "tool_call_id" and (function) "name" key, and the "metadata" key should
   * be removed. The "encoding" key should also be removed.
   *
   * @param chatHistory - The chat history to prepare
   * @param roleKey - The key name for the role/author
   * @param contentKey - The key name for the content/message
   * @returns The prepared chat history for a request
   */
  protected _prepareChatHistoryForRequest(
    chatHistory: ChatHistory,
    roleKey: string = 'role',
    contentKey: string = 'content'
  ): any[] {
    // Handle case where chatHistory might be wrapped in an object with chatHistory and settings keys
    let actualChatHistory = chatHistory
    if ('chatHistory' in (chatHistory as any) && 'settings' in (chatHistory as any)) {
      logger.debug('ChatHistory parameter appears wrapped, extracting actual ChatHistory')
      actualChatHistory = (chatHistory as any).chatHistory as ChatHistory
    }

    return actualChatHistory.messages
      .filter((message) => !(message instanceof AnnotationContent) && !(message instanceof FileReferenceContent))
      .map((message) => {
        const dict = message.toDict(roleKey, contentKey)

        // Override system role with developer if instructionRole is set to 'developer'
        if (this.instructionRole === 'developer' && dict[roleKey] === 'system') {
          return {
            ...dict,
            [roleKey]: 'developer',
          }
        }

        return dict
      })
  }

  // #endregion

  // #region Function calling

  /**
   * Process a function call (deprecated - use kernel.invokeFunction instead).
   *
   * @deprecated Use `invoke_function_call` from the kernel instead with `FunctionChoiceBehavior`.
   */
  protected async _processFunctionCall(
    _functionCall: FunctionCallContent,
    _chatHistory: ChatHistory,
    _kernel: Kernel,
    _args: KernelArguments | null,
    _functionCallCount: number,
    _requestIndex: number,
    _functionCallBehavior: FunctionChoiceBehavior
  ): Promise<AutoFunctionInvocationContext | null> {
    // This method should delegate to the kernel's function invocation logic
    // The exact implementation depends on the kernel's API
    return null
  }

  // #endregion

  // #region Type guards

  /**
   * Type guard to check if response is a ChatCompletion.
   */
  private _isChatCompletion(response: any): boolean {
    return response && 'choices' in response && !(Symbol.asyncIterator in response)
  }

  /**
   * Type guard to check if response is a Stream.
   */
  private _isStream(response: any): boolean {
    return response && Symbol.asyncIterator in response
  }

  // #endregion
}
