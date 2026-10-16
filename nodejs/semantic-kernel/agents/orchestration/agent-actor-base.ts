import { ChatHistory } from '../../contents/chat-history'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { createDefaultLogger } from '../../utils/logger'
import { Agent, AgentThread } from '../agent'
import { MessageContext } from '../runtime/core/message-context'
import { RoutedAgent } from '../runtime/core/routed-agent'
import { DefaultTypeAlias } from './orchestration-base'

const logger = createDefaultLogger('AgentActorBase')

/**
 * A base class for actors running in the AgentRuntime.
 */
export abstract class ActorBase extends RoutedAgent {
  protected _exceptionCallback: (exception: Error) => void

  /**
   * Initialize the actor with a description and an exception callback.
   *
   * @param description - A description of the actor
   * @param exceptionCallback - A callback function to handle exceptions
   */
  constructor(description: string, exceptionCallback: (exception: Error) => void) {
    super(description)
    this._exceptionCallback = exceptionCallback
  }

  /**
   * Handle a message.
   * Stop the handling of the message if the cancellation token is cancelled.
   */
  async onMessageImpl(message: any, ctx: MessageContext): Promise<any> {
    if (ctx.cancellationToken.isCancelled()) {
      return undefined
    }

    return await super.onMessageImpl(message, ctx)
  }

  /**
   * Decorator that wraps a method in a try-catch block and calls the exception callback on errors.
   * This decorator can be used on both synchronous and asynchronous methods.
   *
   * @param target - The target object
   * @param propertyKey - The name of the method
   * @param descriptor - The method descriptor
   */
  protected static exceptionHandler(
    _target: any,
    _propertyKey: string,
    descriptor: PropertyDescriptor
  ): PropertyDescriptor {
    const originalMethod = descriptor.value

    descriptor.value = async function (this: ActorBase, ...args: any[]) {
      try {
        return await originalMethod.apply(this, args)
      } catch (error) {
        this._exceptionCallback(error as Error)
        logger.error(`Exception occurred in agent ${this.id}:`, error)
        throw error
      }
    }

    return descriptor
  }
}

/**
 * A agent actor for multi-agent orchestration running on Agent runtime.
 */
export class AgentActorBase extends ActorBase {
  protected _agent: Agent
  protected _internalTopicType: string
  protected _agentResponseCallback?: (response: DefaultTypeAlias) => void | Promise<void>
  protected _streamingAgentResponseCallback?: (
    response: StreamingChatMessageContent,
    isFinal: boolean
  ) => void | Promise<void>

  protected _agentThread?: AgentThread
  protected _messageCache: ChatHistory

  /**
   * Initialize the agent container.
   *
   * @param agent - An agent to be run in the container
   * @param internalTopicType - The topic type of the internal topic
   * @param exceptionCallback - A function that is called when an exception occurs
   * @param agentResponseCallback - A function that is called when a full response is produced by the agents
   * @param streamingAgentResponseCallback - A function that is called when a streaming response is produced by the agents
   */
  constructor(options: {
    agent: Agent
    internalTopicType: string
    exceptionCallback: (exception: Error) => void
    agentResponseCallback?: (response: DefaultTypeAlias) => void | Promise<void>
    streamingAgentResponseCallback?: (response: StreamingChatMessageContent, isFinal: boolean) => void | Promise<void>
  }) {
    super(options.agent.description ?? 'Semantic Kernel Actor', options.exceptionCallback)

    this._agent = options.agent
    this._internalTopicType = options.internalTopicType
    this._agentResponseCallback = options.agentResponseCallback
    this._streamingAgentResponseCallback = options.streamingAgentResponseCallback

    this._messageCache = new ChatHistory()
  }

  /**
   * Call the agent_response_callback function if it is set.
   *
   * @param message - The message to be sent to the agent_response_callback
   */
  protected async _callAgentResponseCallback(message: DefaultTypeAlias): Promise<void> {
    if (this._agentResponseCallback) {
      await this._agentResponseCallback(message)
    }
  }

  /**
   * Call the streaming_agent_response_callback function if it is set.
   *
   * @param messageChunk - The message chunk
   * @param isFinal - Whether this is the final chunk of the response
   */
  protected async _callStreamingAgentResponseCallback(
    messageChunk: StreamingChatMessageContent,
    isFinal: boolean
  ): Promise<void> {
    if (this._streamingAgentResponseCallback) {
      await this._streamingAgentResponseCallback(messageChunk, isFinal)
    }
  }

  /**
   * Invoke the agent with the current chat history or thread and optionally additional messages.
   *
   * @param additionalMessages - Additional messages to be sent to the agent
   * @param kwargs - Additional keyword arguments to be passed to the agent's invoke method
   * @returns The response from the agent
   */
  protected async _invokeAgent(
    additionalMessages?: DefaultTypeAlias,
    kwargs?: Record<string, any>
  ): Promise<ChatMessageContent> {
    try {
      const streamingMessageBuffer: StreamingChatMessageContent[] = []
      const messages = this._createMessages(additionalMessages)

      for await (const responseItem of this._agent.invokeStream({
        messages,
        thread: this._agentThread,
        onIntermediateMessage: this._handleIntermediateMessage.bind(this),
        ...kwargs,
      })) {
        // Buffer message chunks and stream them with correct is_final flag
        streamingMessageBuffer.push(responseItem.message)
        if (streamingMessageBuffer.length > 1) {
          await this._callStreamingAgentResponseCallback(
            streamingMessageBuffer[streamingMessageBuffer.length - 2],
            false
          )
        }
        if (!this._agentThread) {
          this._agentThread = responseItem.thread
        }
      }

      if (streamingMessageBuffer.length > 0) {
        // Call the callback for the last message chunk with is_final=True
        await this._callStreamingAgentResponseCallback(streamingMessageBuffer[streamingMessageBuffer.length - 1], true)
      }

      if (streamingMessageBuffer.length === 0) {
        throw new Error(`Agent "${this._agent.name}" did not return any response.`)
      }

      // Build the full response from the streaming messages
      let fullResponse = streamingMessageBuffer[0]
      for (let i = 1; i < streamingMessageBuffer.length; i++) {
        // Concatenate streaming messages
        fullResponse = new StreamingChatMessageContent({
          role: fullResponse.role,
          choiceIndex: fullResponse.choiceIndex,
          content: (fullResponse.content ?? '') + (streamingMessageBuffer[i].content ?? ''),
          name: fullResponse.name,
          items: [...(fullResponse.items ?? []), ...(streamingMessageBuffer[i].items ?? [])],
          metadata: { ...fullResponse.metadata, ...streamingMessageBuffer[i].metadata },
          encoding: fullResponse.encoding,
          innerContent: fullResponse.innerContent,
          finishReason: fullResponse.finishReason,
          aiModelId: fullResponse.aiModelId,
        })
      }

      await this._callAgentResponseCallback(fullResponse)

      return fullResponse
    } catch (error) {
      this._exceptionCallback(error as Error)
      logger.error(`Exception occurred in agent ${this.id}:`, error)
      throw error
    }
  }

  /**
   * Create a list of messages to be sent to the agent along with a potential thread.
   *
   * @param additionalMessages - Additional messages to be sent to the agent
   * @returns A list of messages to be sent to the agent
   */
  protected _createMessages(additionalMessages?: DefaultTypeAlias): ChatMessageContent[] {
    const baseMessages = [...this._messageCache.messages]

    // Clear the message cache for the next invoke
    this._messageCache.messages = []

    if (!additionalMessages) {
      return baseMessages
    }

    if (Array.isArray(additionalMessages)) {
      return [...baseMessages, ...additionalMessages]
    }
    return [...baseMessages, additionalMessages]
  }

  /**
   * Handle intermediate messages from the agent.
   */
  protected async _handleIntermediateMessage(message: ChatMessageContent): Promise<void> {
    await this._callAgentResponseCallback(message)

    if (message instanceof StreamingChatMessageContent) {
      await this._callStreamingAgentResponseCallback(message, true)
    } else {
      // Convert to StreamingChatMessageContent if needed
      const streamingMessage = new StreamingChatMessageContent({
        role: message.role,
        choiceIndex: 0,
        items: message.items,
        content: message.content,
        name: message.name,
        innerContent: message.innerContent,
        encoding: message.encoding,
        finishReason: message.finishReason,
        aiModelId: message.aiModelId,
        metadata: message.metadata,
      })
      await this._callStreamingAgentResponseCallback(streamingMessage, true)
    }
  }
}
