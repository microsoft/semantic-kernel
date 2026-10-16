import { ChatMessageContent } from '../../contents/chat-message-content'

/**
 * Defines the communication protocol for a particular Agent type.
 *
 * An agent provides its own AgentChannel via createChannel.
 *
 * @experimental This class is experimental and may change in future versions.
 */
export abstract class AgentChannel {
  /**
   * Receive the conversation messages.
   *
   * Used when joining a conversation and also during each agent interaction.
   *
   * @param history - The history of messages in the conversation
   */
  abstract receive(history: ChatMessageContent[]): Promise<void>

  /**
   * Perform a discrete incremental interaction between a single Agent and AgentChat.
   *
   * @param agent - The agent to interact with
   * @param kwargs - Additional keyword arguments
   * @returns An async iterable of tuples containing a boolean and ChatMessageContent
   */
  abstract invoke(agent: any, kwargs?: Record<string, any>): AsyncIterable<[boolean, ChatMessageContent]>

  /**
   * Perform a discrete incremental stream interaction between a single Agent and AgentChat.
   *
   * @param agent - The agent to interact with
   * @param messages - The history of messages in the conversation
   * @param kwargs - Additional keyword arguments
   * @returns An async iterable of ChatMessageContent
   */
  abstract invokeStream(
    agent: any,
    messages: ChatMessageContent[],
    kwargs?: Record<string, any>
  ): AsyncIterable<ChatMessageContent>

  /**
   * Retrieve the message history specific to this channel.
   *
   * @returns An async iterable of ChatMessageContent
   */
  abstract getHistory(): AsyncIterable<ChatMessageContent>

  /**
   * Reset any persistent state associated with the channel.
   */
  abstract reset(): Promise<void>
}
