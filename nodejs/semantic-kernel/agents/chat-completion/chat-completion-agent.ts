// Copyright (c) Microsoft. All rights reserved.

import { randomUUID } from 'crypto'
import { ChatCompletionClientBase } from '../../connectors/ai/chat-completion-client-base'
import { FunctionChoiceBehavior } from '../../connectors/ai/function-choice-behavior'
import { PromptExecutionSettings } from '../../connectors/ai/prompt-execution-settings'
import { ChatHistory } from '../../contents/chat-history'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { FunctionCallContent } from '../../contents/function-call-content'
import { FunctionResultContent } from '../../contents/function-result-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { AuthorRole } from '../../contents/utils/author-role'
import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel } from '../../kernel'
import { createDefaultLogger } from '../../utils/logger'
import { Agent, AgentConfig, AgentResponseItem, AgentThread, IntermediateMessageCallback } from '../agent'
import { AgentChannel } from '../channels/agent-channel'
import { ChatHistoryChannel } from '../channels/chat-history-channel'

const logger = createDefaultLogger('ChatCompletionAgent')

/**
 * Chat History Agent Thread class.
 */
export class ChatHistoryAgentThread extends AgentThread {
  private _chatHistory: ChatHistory

  /**
   * Creates a new ChatHistoryAgentThread instance.
   * @param chatHistory - The chat history for the thread. If not provided, a new ChatHistory instance will be created.
   * @param threadId - The ID of the thread. If not provided, a new thread will be created.
   */
  constructor(chatHistory?: ChatHistory, threadId?: string) {
    super()
    this._chatHistory = chatHistory ?? new ChatHistory()
    this._id = threadId ?? `thread_${randomUUID()}`
  }

  /**
   * Returns the length of the chat history.
   */
  get length(): number {
    return this._chatHistory.messages.length
  }

  /**
   * Starts the thread and returns its ID.
   */
  protected async _create(): Promise<string> {
    return this._id!
  }

  /**
   * Ends the current thread.
   */
  protected async _delete(): Promise<void> {
    this._chatHistory.messages = []
  }

  /**
   * Called when a new message has been contributed to the chat.
   */
  protected async _onNewMessage(newMessage: string | ChatMessageContent): Promise<void> {
    let message: ChatMessageContent

    if (typeof newMessage === 'string') {
      message = new ChatMessageContent({
        role: AuthorRole.USER,
        content: newMessage,
      })
    } else {
      message = newMessage
    }

    // Only add the message if it doesn't already have the thread_id metadata
    // or if it has a different thread_id
    if (!message.metadata || !message.metadata['thread_id'] || message.metadata['thread_id'] !== this._id) {
      this._chatHistory.addMessage(message)
    }
  }

  /**
   * Retrieve the current chat history.
   */
  async *getMessages(): AsyncIterable<ChatMessageContent> {
    if (this._isDeleted) {
      throw new Error('Cannot retrieve chat history, since the thread has been deleted.')
    }

    if (this._id === undefined) {
      await this.create()
    }

    for (const message of this._chatHistory.messages) {
      yield message
    }
  }
}

/**
 * Configuration for ChatCompletionAgent.
 */
export interface ChatCompletionAgentConfig extends AgentConfig {
  service?: ChatCompletionClientBase
  functionChoiceBehavior?: FunctionChoiceBehavior
}

/**
 * A Chat Completion Agent based on ChatCompletionClientBase.
 */
export class ChatCompletionAgent extends Agent {
  public static override channelType: new () => AgentChannel = ChatHistoryChannel as any

  public service?: ChatCompletionClientBase
  public functionChoiceBehavior?: FunctionChoiceBehavior

  /**
   * Creates a new ChatCompletionAgent instance.
   * @param config - The agent configuration
   */
  constructor(config: ChatCompletionAgentConfig = {}) {
    super(config)

    this.service = config.service
    this.functionChoiceBehavior = config.functionChoiceBehavior ?? FunctionChoiceBehavior.Auto()

    // Configure the service if provided
    if (this.service) {
      if (!(this.service instanceof ChatCompletionClientBase)) {
        throw new Error(
          `Service provided for ChatCompletionAgent is not an instance of ChatCompletionClientBase. Service: ${typeof this.service}`
        )
      }
      const serviceId = this.service.serviceId ?? 'chat_completion'
      this.kernel.addService(serviceId, this.service)
    }
  }

  /**
   * Create a ChatHistoryChannel.
   * @param chatHistory - The chat history for the channel
   * @param threadId - The ID of the thread
   * @returns An instance of AgentChannel
   */
  async createChannel(chatHistory?: ChatHistory, threadId?: string): Promise<AgentChannel> {
    const thread = new ChatHistoryAgentThread(chatHistory, threadId)

    if (!thread.id) {
      await thread.create()
    }

    const messages: ChatMessageContent[] = []
    for await (const message of thread.getMessages()) {
      messages.push(message)
    }

    return new ChatHistoryChannel(chatHistory)
  }

  /**
   * Get a response from the agent.
   * @param options - The invocation options
   * @returns An AgentResponseItem of type ChatMessageContent
   */
  async getResponse(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    arguments?: KernelArguments
    kernel?: Kernel
    [key: string]: any
  }): Promise<AgentResponseItem<ChatMessageContent>> {
    const thread = await this._ensureThreadExistsWithMessages({
      messages: options.messages,
      thread: options.thread,
      constructThread: () => new ChatHistoryAgentThread(),
      expectedType: ChatHistoryAgentThread,
    })

    const chatHistory = new ChatHistory()
    for await (const message of thread.getMessages()) {
      chatHistory.addMessage(message)
    }

    const responses: ChatMessageContent[] = []
    for await (const response of this._innerInvoke(thread, chatHistory, undefined, options.arguments, options.kernel)) {
      responses.push(response)
    }

    if (responses.length === 0) {
      throw new Error('No response from agent.')
    }

    return new AgentResponseItem(responses[responses.length - 1], thread)
  }

  /**
   * Invoke the chat history handler.
   * @param options - The invocation options
   * @returns An async iterable of AgentResponseItem of type ChatMessageContent
   */
  async *invoke(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    onIntermediateMessage?: IntermediateMessageCallback
    arguments?: KernelArguments
    kernel?: Kernel
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
    const thread = await this._ensureThreadExistsWithMessages({
      messages: options.messages,
      thread: options.thread,
      constructThread: () => new ChatHistoryAgentThread(),
      expectedType: ChatHistoryAgentThread,
    })

    const chatHistory = new ChatHistory()
    for await (const message of thread.getMessages()) {
      chatHistory.addMessage(message)
    }

    for await (const response of this._innerInvoke(
      thread,
      chatHistory,
      options.onIntermediateMessage,
      options.arguments,
      options.kernel
    )) {
      yield new AgentResponseItem(response, thread)
    }
  }

  /**
   * Invoke the chat history handler in streaming mode.
   * @param options - The invocation options
   * @returns An async generator of AgentResponseItem of type StreamingChatMessageContent
   */
  async *invokeStream(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    onIntermediateMessage?: IntermediateMessageCallback
    arguments?: KernelArguments
    kernel?: Kernel
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
    const thread = await this._ensureThreadExistsWithMessages({
      messages: options.messages,
      thread: options.thread,
      constructThread: () => new ChatHistoryAgentThread(),
      expectedType: ChatHistoryAgentThread,
    })

    const chatHistory = new ChatHistory()
    for await (const message of thread.getMessages()) {
      chatHistory.addMessage(message)
    }

    const args = options.arguments ?? new KernelArguments()
    const kernel = options.kernel ?? this.kernel
    const mergedArguments = this._mergeArguments(args)

    const [chatCompletionService, settings] = await this._getChatCompletionServiceAndSettings(kernel, mergedArguments)

    // If the user hasn't provided a function choice behavior, use the agent's default
    if (!settings.functionChoiceBehavior) {
      settings.functionChoiceBehavior = this.functionChoiceBehavior
    }

    const agentChatHistory = await this._prepareAgentChatHistory(chatHistory, kernel, mergedArguments)

    const messageCountBeforeCompletion = agentChatHistory.messages.length

    logger.debug(`[${this.constructor.name}] Invoking ${chatCompletionService.constructor.name}.`)

    const responses = chatCompletionService.getStreamingChatMessageContents(agentChatHistory, settings, {
      kernel,
      arguments: mergedArguments,
    })

    logger.debug(
      `[${this.constructor.name}] Invoked ${chatCompletionService.constructor.name} with message count: ${messageCountBeforeCompletion}.`
    )

    let role: AuthorRole | undefined
    const responseBuilder: string[] = []
    let startIdx = agentChatHistory.messages.length

    for await (const responseList of responses) {
      for (const response of responseList) {
        role = response.role
        response.name = this.name
        responseBuilder.push(response.content ?? '')

        if (
          role === AuthorRole.ASSISTANT &&
          (response.items?.length > 0 || response.metadata?.['usage']) &&
          !response.items?.some((item) => item instanceof FunctionCallContent || item instanceof FunctionResultContent)
        ) {
          yield new AgentResponseItem(response, thread)
        }
      }

      // Drain newly added tool messages since last index to maintain
      // correct order and avoid duplicates
      const newMessages = await this._drainMutatedMessages(agentChatHistory, startIdx, thread)

      // Resets startIdx to the latest length of agentChatHistory
      startIdx = agentChatHistory.messages.length

      if (options.onIntermediateMessage) {
        for (const message of newMessages) {
          await options.onIntermediateMessage(message)
        }
      }
    }

    if (role !== AuthorRole.TOOL) {
      // Tool messages will be automatically added to the chat history by the auto function invocation loop
      // if it's the response (i.e. terminated by a filter), thus we need to avoid notifying the thread about
      // them multiple times.
      await thread.onNewMessage(
        new ChatMessageContent({
          role: role ?? AuthorRole.ASSISTANT,
          content: responseBuilder.join(''),
          name: this.name,
        })
      )
    }
  }

  /**
   * Helper method to invoke the agent with a chat history in non-streaming mode.
   */
  private async *_innerInvoke(
    thread: ChatHistoryAgentThread,
    history: ChatHistory,
    onIntermediateMessage?: IntermediateMessageCallback,
    arguments_?: KernelArguments,
    kernel?: Kernel
  ): AsyncIterable<ChatMessageContent> {
    const args = arguments_ ?? new KernelArguments()
    const kernelInstance = kernel ?? this.kernel
    const mergedArguments = this._mergeArguments(args)

    const [chatCompletionService, settings] = await this._getChatCompletionServiceAndSettings(
      kernelInstance,
      mergedArguments
    )

    // If the user hasn't provided a function choice behavior, use the agent's default
    if (!settings.functionChoiceBehavior) {
      settings.functionChoiceBehavior = this.functionChoiceBehavior
    }

    const agentChatHistory = await this._prepareAgentChatHistory(history, kernelInstance, mergedArguments)

    const startIdx = agentChatHistory.messages.length
    const messageCountBeforeCompletion = agentChatHistory.messages.length

    logger.debug(`[${this.constructor.name}] Invoking ${chatCompletionService.constructor.name}.`)

    const responses = await chatCompletionService.getChatMessageContents(agentChatHistory, settings, {
      kernel: kernelInstance,
      arguments: mergedArguments,
    })

    logger.debug(
      `[${this.constructor.name}] Invoked ${chatCompletionService.constructor.name} with message count: ${messageCountBeforeCompletion}.`
    )

    // Drain newly added tool messages since last index to maintain
    // correct order and avoid duplicates
    const newMsgs = await this._drainMutatedMessages(agentChatHistory, startIdx, thread)

    if (onIntermediateMessage) {
      for (const msg of newMsgs) {
        await onIntermediateMessage(msg)
      }
    }

    for (const response of responses) {
      response.name = this.name
      if (response.role !== AuthorRole.TOOL) {
        // Tool messages will be automatically added to the chat history by the auto function invocation loop
        // if it's the response (i.e. terminated by a filter), thus we need to avoid notifying the thread about
        // them multiple times.
        await thread.onNewMessage(response)
      }
      yield response
    }
  }

  /**
   * Prepare the agent chat history from the input history by adding the formatted instructions.
   */
  private async _prepareAgentChatHistory(
    history: ChatHistory,
    kernel: Kernel,
    arguments_: KernelArguments
  ): Promise<ChatHistory> {
    const formattedInstructions = await this.formatInstructions(kernel, arguments_)
    const messages: ChatMessageContent[] = []

    if (formattedInstructions) {
      messages.push(
        new ChatMessageContent({
          role: AuthorRole.SYSTEM,
          content: formattedInstructions,
          name: this.name,
        })
      )
    }

    if (history.messages.length > 0) {
      messages.push(...history.messages)
    }

    return new ChatHistory(messages)
  }

  /**
   * Get the chat completion service and settings.
   */
  private async _getChatCompletionServiceAndSettings(
    kernel: Kernel,
    arguments_: KernelArguments
  ): Promise<[ChatCompletionClientBase, PromptExecutionSettings]> {
    const service = kernel.getService<ChatCompletionClientBase>(undefined, ChatCompletionClientBase as any)

    if (!service) {
      throw new Error('Chat completion service not found. Check your service or kernel configuration.')
    }

    // Get settings from arguments or create default
    const settings = arguments_.executionSettings?.[0] ?? new PromptExecutionSettings()

    return [service, settings]
  }

  /**
   * Return messages appended to history after start and push them to thread.
   */
  private async _drainMutatedMessages(
    history: ChatHistory,
    start: number,
    thread: ChatHistoryAgentThread
  ): Promise<ChatMessageContent[]> {
    const drained: ChatMessageContent[] = []

    for (let i = start; i < history.messages.length; i++) {
      const msg = history.messages[i]
      msg.name = this.name
      await thread.onNewMessage(msg)
      drained.push(msg)
    }

    return drained
  }
}
