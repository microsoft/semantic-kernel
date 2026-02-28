import { ChatHistory } from '../../contents/chat-history'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { FunctionCallContent } from '../../contents/function-call-content'
import { FunctionResultContent } from '../../contents/function-result-content'
import { ImageContent } from '../../contents/image-content'
import { StreamingTextContent } from '../../contents/streaming-text-content'
import { TextContent } from '../../contents/text-content'
import { Agent } from '../agent'
import { AgentChannel } from './agent-channel'

/**
 * A channel that maintains chat history for agent interactions.
 */
export class ChatHistoryChannel extends AgentChannel {
  /**
   * The allowed content types for this channel.
   */
  public static readonly ALLOWED_CONTENT_TYPES: Set<new (...args: any[]) => any> = new Set([
    ImageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingTextContent,
    TextContent,
  ])

  private readonly _history: ChatHistory
  private readonly _messageQueue: ChatMessageContent[] = []

  /**
   * Creates a new ChatHistoryChannel instance.
   * @param history - The chat history to use for this channel
   */
  constructor(history?: ChatHistory) {
    super()
    this._history = history ?? new ChatHistory()
  }

  /**
   * Receives messages from the agent.
   * @param history - The message history to receive from
   */
  public async receive(history: ChatMessageContent[]): Promise<void> {
    for (const message of history) {
      if (this._isContentTypeAllowed(message)) {
        this._messageQueue.push(message)
        this._history.addMessage(message)
      }
    }
  }

  /**
   * Invokes the agent to produce a response.
   * @param agent - The agent to invoke
   * @param kwargs - Additional keyword arguments
   * @yields Tuples of [boolean, ChatMessageContent] where boolean indicates if more messages will follow
   */
  public async *invoke(agent: Agent, kwargs?: Record<string, any>): AsyncIterable<[boolean, ChatMessageContent]> {
    const messages = kwargs?.messages as string | ChatMessageContent | Array<string | ChatMessageContent> | undefined

    // Invoke the agent with the messages
    for await (const responseItem of agent.invoke({ messages: messages ?? this._history.messages })) {
      const message = responseItem.message

      // Clone the message and update its metadata
      const updatedMessage = new ChatMessageContent({
        role: message.role,
        content: message.content,
        name: message.name,
        items: message.items,
        encoding: message.encoding,
        metadata: {
          ...message.metadata,
          agent_hash: this._getAgentHash(agent),
        },
      })

      this._messageQueue.push(updatedMessage)
      this._history.addMessage(updatedMessage)

      // Yield [boolean, message] where boolean indicates if more messages will follow
      yield [true, updatedMessage]
    }
  }

  /**
   * Invokes the agent to produce a streaming response.
   * @param agent - The agent to invoke
   * @param messages - The message history
   * @yields The chat messages
   */
  public async *invokeStream(agent: Agent, messages: ChatMessageContent[]): AsyncIterable<ChatMessageContent> {
    let fullMessage: ChatMessageContent | undefined

    for await (const responseItem of agent.invokeStream({ messages })) {
      const streamingMessage = responseItem.message

      // For streaming content, accumulate the message
      if (!fullMessage) {
        fullMessage = new ChatMessageContent({
          role: streamingMessage.role,
          content: streamingMessage.content,
          name: streamingMessage.name,
          items: streamingMessage.items,
          encoding: streamingMessage.encoding,
          metadata: {
            ...streamingMessage.metadata,
          },
        })
      } else {
        // Append content to the existing message
        if (streamingMessage.content) {
          fullMessage = new ChatMessageContent({
            role: fullMessage.role,
            content: (fullMessage.content ?? '') + streamingMessage.content,
            name: fullMessage.name,
            items: fullMessage.items,
            encoding: fullMessage.encoding,
            metadata: fullMessage.metadata,
          })
        }
      }

      yield streamingMessage
    }

    // Add the complete message to history and queue
    if (fullMessage) {
      const updatedMessage = new ChatMessageContent({
        role: fullMessage.role,
        content: fullMessage.content,
        name: fullMessage.name,
        items: fullMessage.items,
        encoding: fullMessage.encoding,
        metadata: {
          ...fullMessage.metadata,
          agent_hash: this._getAgentHash(agent),
        },
      })

      this._messageQueue.push(updatedMessage)
      this._history.addMessage(updatedMessage)
    }
  }

  /**
   * Gets the chat history.
   * @returns The chat history messages in reverse order
   */
  public async *getHistory(): AsyncIterable<ChatMessageContent> {
    // Return messages in reverse order (most recent first)
    for (let i = this._history.messages.length - 1; i >= 0; i--) {
      yield this._history.messages[i]
    }
  }

  /**
   * Resets the channel by clearing the message history.
   */
  public async reset(): Promise<void> {
    this._history.messages = []
    this._messageQueue.length = 0
  }

  /**
   * Checks if a message contains only allowed content types.
   * @param message - The message to check
   * @returns True if all content is allowed, false otherwise
   */
  private _isContentTypeAllowed(message: ChatMessageContent): boolean {
    if (!message.items || message.items.length === 0) {
      return true
    }

    for (const item of message.items) {
      const itemConstructor = item.constructor as new (...args: any[]) => any
      if (!ChatHistoryChannel.ALLOWED_CONTENT_TYPES.has(itemConstructor)) {
        return false
      }
    }

    return true
  }

  /**
   * Gets a hash code for the agent.
   * @param agent - The agent to hash
   * @returns A hash code as a number
   */
  private _getAgentHash(agent: Agent): number {
    // Simple hash based on agent id and name
    const str = `${agent.id}:${agent.name}`
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = (hash << 5) - hash + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return hash
  }
}
