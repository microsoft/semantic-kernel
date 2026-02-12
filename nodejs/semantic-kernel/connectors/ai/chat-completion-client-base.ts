import { AnnotationContent } from '../../contents/annotation-content'
import { ChatHistory } from '../../contents/chat-history'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { FileReferenceContent } from '../../contents/file-reference-content'
import { FunctionCallContent } from '../../contents/function-call-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { Kernel, KernelArguments } from '../../kernel'
import { AIServiceClientBase, PromptExecutionSettings } from '../../services/ai-service-client-base'
import { Logger, createDefaultLogger } from '../../utils/logger'
import { FunctionCallChoiceConfiguration } from './function-call-choice-configuration'
import { FunctionChoiceType } from './function-choice-type'

const logger: Logger = createDefaultLogger('ChatCompletionClientBase')

const AUTO_FUNCTION_INVOCATION_SPAN_NAME = 'auto_function_invocation'

/**
 * Base class for chat completion AI services.
 */
export abstract class ChatCompletionClientBase extends AIServiceClientBase {
  /**
   * Connectors that support function calling should set this to true.
   */
  static readonly SUPPORTS_FUNCTION_CALLING: boolean = false

  /**
   * The role for instructions.
   */
  instructionRole: string = 'system'

  // #region Internal methods to be implemented by derived classes

  /**
   * Send a chat request to the AI service.
   * This method must be implemented by derived classes.
   *
   * @param chatHistory - The chat history to send
   * @param settings - The settings for the request
   * @returns The chat message contents representing the response(s)
   */
  protected abstract _innerGetChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings
  ): Promise<ChatMessageContent[]>

  /**
   * Send a streaming chat request to the AI service.
   * This method must be implemented by derived classes.
   *
   * @param chatHistory - The chat history to send
   * @param settings - The settings for the request
   * @param functionInvokeAttempt - The current attempt count for automatically invoking functions
   * @returns An async generator yielding streaming chat message contents
   */
  protected abstract _innerGetStreamingChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings,
    functionInvokeAttempt?: number
  ): AsyncGenerator<StreamingChatMessageContent[], void>

  // #endregion

  // #region Public methods

  /**
   * Create chat message contents, in the number specified by the settings.
   *
   * @param chatHistory - A chat history object containing messages from system, user, assistant and tools
   * @param settings - Settings for the request
   * @param kwargs - Optional arguments including kernel
   * @returns A list of chat message contents representing the response(s) from the LLM
   */
  async getChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings,
    kwargs?: { kernel?: Kernel; arguments?: KernelArguments; [key: string]: any }
  ): Promise<ChatMessageContent[]> {
    // Note: function-calling-utils import commented out until the module is created
    // const { mergeFunctionResults } = await import('./function-calling-utils');
    const mergeFunctionResults = (messages: any[]) => messages

    // Create a copy of the settings to avoid modifying the original settings
    settings = this._deepCopy(settings)

    // Cast to the proper settings class if needed
    const SettingsClass = this.getPromptExecutionSettingsClass()
    if (!(settings instanceof SettingsClass)) {
      settings = this.getPromptExecutionSettingsFromSettings(settings)
    }

    const supportsFC = (this.constructor as typeof ChatCompletionClientBase).SUPPORTS_FUNCTION_CALLING
    if (!supportsFC) {
      return await this._innerGetChatMessageContents(chatHistory, settings)
    }

    const kernel = kwargs?.kernel
    const functionChoiceBehavior = (settings as any).functionChoiceBehavior

    if (functionChoiceBehavior !== undefined && functionChoiceBehavior !== null) {
      if (!kernel) {
        throw new Error('The kernel is required for function calls.')
      }
      this._verifyFunctionChoiceSettings(settings)
    }

    if (functionChoiceBehavior && kernel) {
      // Configure the function choice behavior into the settings object
      functionChoiceBehavior.configure({
        kernel,
        updateSettingsCallback: this._updateFunctionChoiceSettingsCallback(),
        settings,
      })
    }

    if (!functionChoiceBehavior || !functionChoiceBehavior.autoInvokeKernelFunctions) {
      return await this._innerGetChatMessageContents(chatHistory, settings)
    }

    // Auto invoke loop
    const span = this._startAutoFunctionInvocationActivity(kernel!, settings)
    try {
      const maxAttempts = functionChoiceBehavior.maximumAutoInvokeAttempts || 5

      for (let requestIndex = 0; requestIndex < maxAttempts; requestIndex++) {
        const completions = await this._innerGetChatMessageContents(chatHistory, settings)

        // Get the function call contents from the chat message
        const functionCalls = completions[0].items.filter(
          (item) => item instanceof FunctionCallContent
        ) as FunctionCallContent[]

        const fcCount = functionCalls.length
        if (fcCount === 0) {
          return completions
        }

        // Add the assistant's tool call message to the history
        chatHistory.addMessage(completions[0])

        logger.info(`Processing ${fcCount} tool calls in parallel.`)

        // Invoke all function calls in parallel
        const results = await Promise.all(
          functionCalls.map((functionCall) =>
            kernel!.invokeFunctionCall({
              functionCall: functionCall as any,
              chatHistory,
              arguments: kwargs?.arguments,
              executionSettings: settings,
              functionCallCount: fcCount,
              requestIndex,
              functionBehavior: functionChoiceBehavior,
            })
          )
        )

        if (results.some((result: any) => result?.terminate)) {
          const lastMessages = chatHistory.messages.slice(-results.length)
          return mergeFunctionResults(lastMessages)
        }
      }

      // Do a final call without function calling when max has been reached
      this._resetFunctionChoiceSettings(settings)
      return await this._innerGetChatMessageContents(chatHistory, settings)
    } finally {
      // End span
      span?.end?.()
    }
  }

  /**
   * Get a single chat message content from the LLM.
   *
   * @param chatHistory - The chat history
   * @param settings - Settings for the request
   * @param kwargs - Optional arguments
   * @returns A single chat message content or null
   */
  async getChatMessageContent(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings,
    kwargs?: { kernel?: Kernel; arguments?: KernelArguments; [key: string]: any }
  ): Promise<ChatMessageContent | null> {
    const results = await this.getChatMessageContents(chatHistory, settings, kwargs)
    return results.length > 0 ? results[0] : null
  }

  /**
   * Create streaming chat message contents, in the number specified by the settings.
   *
   * @param chatHistory - The chat history
   * @param settings - Settings for the request
   * @param kwargs - Optional arguments
   * @returns An async generator yielding streaming chat message contents
   */
  async *getStreamingChatMessageContents(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings,
    kwargs?: { kernel?: Kernel; arguments?: KernelArguments; [key: string]: any }
  ): AsyncGenerator<StreamingChatMessageContent[], void> {
    // Note: function-calling-utils import commented out until the module is created
    // const { mergeStreamingFunctionResults } = await import('./function-calling-utils');
    const mergeStreamingFunctionResults = (messages: any[], _aiModelId?: string, _attempt?: number) => messages

    // Create a copy of the settings to avoid modifying the original settings
    settings = this._deepCopy(settings)

    // Cast to the proper settings class if needed
    const SettingsClass = this.getPromptExecutionSettingsClass()
    if (!(settings instanceof SettingsClass)) {
      settings = this.getPromptExecutionSettingsFromSettings(settings)
    }

    const supportsFC = (this.constructor as typeof ChatCompletionClientBase).SUPPORTS_FUNCTION_CALLING
    if (!supportsFC) {
      yield* this._innerGetStreamingChatMessageContents(chatHistory, settings)
      return
    }

    const kernel = kwargs?.kernel
    const functionChoiceBehavior = (settings as any).functionChoiceBehavior

    if (functionChoiceBehavior !== undefined && functionChoiceBehavior !== null) {
      if (!kernel) {
        throw new Error('The kernel is required for function calls.')
      }
      this._verifyFunctionChoiceSettings(settings)
    }

    if (functionChoiceBehavior && kernel) {
      // Configure the function choice behavior
      functionChoiceBehavior.configure({
        kernel,
        updateSettingsCallback: this._updateFunctionChoiceSettingsCallback(),
        settings,
      })
    }

    if (!functionChoiceBehavior || !functionChoiceBehavior.autoInvokeKernelFunctions) {
      yield* this._innerGetStreamingChatMessageContents(chatHistory, settings)
      return
    }

    // Auto invoke loop
    const span = this._startAutoFunctionInvocationActivity(kernel!, settings)
    try {
      const maxAttempts = functionChoiceBehavior.maximumAutoInvokeAttempts || 5

      for (let requestIndex = 0; requestIndex < maxAttempts; requestIndex++) {
        const allMessages: StreamingChatMessageContent[] = []
        let functionCallReturned = false

        for await (const messages of this._innerGetStreamingChatMessageContents(chatHistory, settings, requestIndex)) {
          for (const msg of messages) {
            if (msg) {
              allMessages.push(msg)
              if (!functionCallReturned && msg.items.some((item) => item instanceof FunctionCallContent)) {
                functionCallReturned = true
              }
            }
          }
          yield messages
        }

        if (!functionCallReturned) {
          return
        }

        // Combine all streaming messages to create the full completion
        const fullCompletion = allMessages.reduce((acc, msg) => acc.add(msg), allMessages[0])
        const functionCalls = fullCompletion.items.filter(
          (item) => item instanceof FunctionCallContent
        ) as FunctionCallContent[]

        chatHistory.addMessage(fullCompletion)

        const fcCount = functionCalls.length
        logger.info(`Processing ${fcCount} tool calls in parallel.`)

        // Invoke all function calls
        const results = await Promise.all(
          functionCalls.map((functionCall) =>
            kernel!.invokeFunctionCall({
              functionCall: functionCall as any,
              chatHistory,
              arguments: kwargs?.arguments,
              isStreaming: true,
              executionSettings: settings,
              functionCallCount: fcCount,
              requestIndex,
              functionBehavior: functionChoiceBehavior,
            })
          )
        )

        // Merge and yield the function results
        const aiModelId = this._getAiModelId(settings)
        const lastMessages = chatHistory.messages.slice(-results.length)
        const functionResultMessages = mergeStreamingFunctionResults(lastMessages, aiModelId, requestIndex)

        if (this._yieldFunctionResultMessages(functionResultMessages)) {
          yield functionResultMessages
        }

        if (results.some((result) => result?.terminate)) {
          break
        }
      }
    } finally {
      // End span
      span?.end?.()
    }
  }

  /**
   * Get a stream of single streaming chat message contents from the LLM.
   *
   * @param chatHistory - The chat history
   * @param settings - Settings for the request
   * @param kwargs - Optional arguments
   * @returns An async generator yielding individual streaming chat message contents
   */
  async *getStreamingChatMessageContent(
    chatHistory: ChatHistory,
    settings: PromptExecutionSettings,
    kwargs?: { kernel?: Kernel; arguments?: KernelArguments; [key: string]: any }
  ): AsyncGenerator<StreamingChatMessageContent | null, void> {
    for await (const contents of this.getStreamingChatMessageContents(chatHistory, settings, kwargs)) {
      yield contents.length > 0 ? contents[0] : null
    }
  }

  // #endregion

  // #region Internal handlers

  /**
   * Prepare the chat history for a request.
   *
   * Override this method to customize the formatting of the chat history for a request.
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
  ): any {
    return chatHistory.messages
      .filter((message) => !(message instanceof AnnotationContent || message instanceof FileReferenceContent))
      .map((message) => message.toDict(roleKey, contentKey))
  }

  /**
   * Additional verification to validate settings for function choice behavior.
   *
   * Override this method to add additional verification for the settings.
   *
   * @param settings - The settings to verify
   */
  protected _verifyFunctionChoiceSettings(_settings: PromptExecutionSettings): void {
    // Default implementation does nothing
  }

  /**
   * Return the callback function to update the settings from a function call configuration.
   *
   * Override this method to provide a custom callback function.
   *
   * @returns The callback function
   */
  protected _updateFunctionChoiceSettingsCallback(): (
    configuration: FunctionCallChoiceConfiguration,
    settings: PromptExecutionSettings,
    choiceType: FunctionChoiceType
  ) => void {
    return () => {
      // Default implementation does nothing
    }
  }

  /**
   * Reset the settings updated by _updateFunctionChoiceSettingsCallback.
   *
   * Override this method to reset the settings.
   *
   * @param settings - The prompt execution settings to reset
   */
  protected _resetFunctionChoiceSettings(_settings: PromptExecutionSettings): void {
    // Default implementation does nothing
  }

  /**
   * Start the auto function invocation activity.
   *
   * @param kernel - The kernel instance
   * @param settings - The prompt execution settings
   * @returns A span object (placeholder for OpenTelemetry integration)
   */
  protected _startAutoFunctionInvocationActivity(
    kernel: Kernel,
    settings: PromptExecutionSettings
  ): { end?: () => void } {
    // Placeholder for OpenTelemetry span
    // In a full implementation, this would create an actual trace span
    const functionChoiceBehavior = (settings as any).functionChoiceBehavior

    if (functionChoiceBehavior) {
      const config = functionChoiceBehavior.getConfig(kernel)
      const availableFunctions = config.availableFunctions || []
      const functionNames = availableFunctions.map((f: any) => f.fullyQualifiedName).join(',')

      logger.info(`${AUTO_FUNCTION_INVOCATION_SPAN_NAME}: ${functionNames}`)
    }

    return {
      end: () => {
        // Placeholder for ending the span
      },
    }
  }

  /**
   * Retrieve the AI model ID from settings if available.
   *
   * @param settings - The prompt execution settings
   * @returns The AI model ID
   */
  protected _getAiModelId(settings: PromptExecutionSettings): string {
    return (settings as any).aiModelId || this.aiModelId
  }

  /**
   * Determine if the function result messages should be yielded.
   *
   * @param functionResultMessages - The function result messages
   * @returns True if the messages should be yielded
   */
  protected _yieldFunctionResultMessages(functionResultMessages: any[]): boolean {
    return functionResultMessages.length > 0 && functionResultMessages[0].items?.length > 0
  }

  /**
   * Deep copy an object.
   *
   * @param obj - The object to copy
   * @returns A deep copy of the object
   */
  protected _deepCopy<T>(obj: T): T {
    if (obj === null || obj === undefined) {
      return obj
    }
    const stringified = JSON.stringify(obj)
    if (stringified === undefined) {
      return obj
    }
    return JSON.parse(stringified)
  }

  // #endregion
}
