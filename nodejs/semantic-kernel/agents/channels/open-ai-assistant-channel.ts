import { ChatMessageContent } from '../../contents/chat-message-content'
import { FileReferenceContent } from '../../contents/file-reference-content'
import { FunctionCallContent } from '../../contents/function-call-content'
import { ImageContent } from '../../contents/image-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { TextContent } from '../../contents/text-content'
import { AuthorRole } from '../../contents/utils/author-role'
import { createDefaultLogger, Logger } from '../../utils/logger'
import { Agent, AgentChannel } from '../agent'

const logger: Logger = createDefaultLogger('OpenAIAssistantChannel')

/**
 * OpenAI Assistant Channel.
 *
 * Provides a channel for communication with OpenAI Assistant agents.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
export class OpenAIAssistantChannel extends AgentChannel {
  private client: any // AsyncOpenAI client type
  private threadId: string

  /**
   * Initialize the OpenAI Assistant Channel.
   *
   * @param options - Configuration options
   * @param options.client - The OpenAI client instance
   * @param options.threadId - The thread ID for this channel
   */
  constructor(options: { client: any; threadId: string }) {
    super()

    if (!options.client) {
      throw new Error('Client cannot be null')
    }

    if (!options.threadId) {
      throw new Error('Thread ID cannot be null')
    }

    this.client = options.client
    this.threadId = options.threadId
  }

  /**
   * Receive conversation messages and add them to the thread.
   *
   * @param history - The conversation messages to receive
   */
  async receive(history: ChatMessageContent[]): Promise<void> {
    for (const message of history) {
      // Skip messages that contain function calls (already in thread)
      if (message.items.some((item) => item instanceof FunctionCallContent)) {
        logger.debug('Skipping message with function call content, already in thread')
        continue
      }

      await this.createChatMessage(message)
    }
  }

  /**
   * Invoke the agent and yield conversation messages.
   *
   * @param agent - The agent to invoke
   * @param kwargs - Additional keyword arguments
   * @yields Tuple of [isVisible, message]
   */
  async *invoke(agent: Agent, kwargs?: Record<string, any>): AsyncIterable<[boolean, ChatMessageContent]> {
    // Import here to avoid circular dependency
    const { OpenAIAssistantAgent } = await import('../open-ai/openai-assistant-agent.js')

    if (!(agent instanceof OpenAIAssistantAgent)) {
      throw new Error(`Agent is not of the expected type OpenAIAssistantAgent`)
    }

    // Use the agent's invoke method with the thread
    const invokeOptions = {
      thread: { id: this.threadId } as any,
      ...(kwargs || {}),
    }

    // Invoke and yield messages
    for await (const responseItem of agent.invoke(invokeOptions)) {
      const isVisible = !responseItem.message.metadata?.code
      yield [isVisible, responseItem.message as any as ChatMessageContent]
    }
  }

  /**
   * Invoke the agent with streaming and yield message chunks.
   *
   * @param agent - The agent to invoke
   * @param kwargs - Additional keyword arguments
   * @yields Streaming chat message content
   */
  async *invokeStream(agent: Agent, kwargs?: Record<string, any>): AsyncIterable<StreamingChatMessageContent> {
    // Import here to avoid circular dependency
    const { OpenAIAssistantAgent } = await import('../open-ai/openai-assistant-agent.js')

    if (!(agent instanceof OpenAIAssistantAgent)) {
      throw new Error(`Agent is not of the expected type OpenAIAssistantAgent`)
    }

    // Use the agent's invokeStream method with the thread
    const streamOptions = {
      thread: { id: this.threadId } as any,
      ...(kwargs || {}),
    }

    // Invoke stream and yield streaming messages
    for await (const responseItem of agent.invokeStream(streamOptions)) {
      yield responseItem.message as any as StreamingChatMessageContent
    }
  }

  /**
   * Get the conversation history from the thread.
   *
   * @yields Chat message content from the thread history
   */
  async *getHistory(): AsyncIterable<ChatMessageContent> {
    const agentNames: Map<string, string> = new Map()

    try {
      const threadMessages = await this.client.beta.threads.messages.list(this.threadId, {
        limit: 100,
        order: 'desc',
      })

      for (const message of threadMessages.data) {
        let assistantName: string | null = null

        // Fetch assistant name if not cached
        if (message.assistant_id && !agentNames.has(message.assistant_id)) {
          try {
            const agent = await this.client.beta.assistants.retrieve(message.assistant_id)
            if (agent.name) {
              agentNames.set(message.assistant_id, agent.name)
            }
          } catch (error) {
            logger.error(`Failed to retrieve assistant with ID ${message.assistant_id}:`, error)
            // If we can't retrieve the assistant, use the ID
            agentNames.set(message.assistant_id, message.assistant_id)
          }
        }

        assistantName = message.assistant_id ? agentNames.get(message.assistant_id) || message.assistant_id : null

        // Generate message content from the thread message
        const content = this.generateMessageContent(assistantName, message)

        if (content?.items && content.items.length > 0) {
          yield content
        }
      }
    } catch (error) {
      throw new Error(`Failed to get thread history: ${error instanceof Error ? error.message : String(error)}`, {
        cause: error,
      })
    }
  }

  /**
   * Reset the agent's thread by deleting it.
   */
  async reset(): Promise<void> {
    try {
      await this.client.beta.threads.delete(this.threadId)
    } catch (error) {
      throw new Error(`Failed to delete thread: ${error instanceof Error ? error.message : String(error)}`, {
        cause: error,
      })
    }
  }

  /**
   * Create a chat message in the thread.
   *
   * @private
   */
  private async createChatMessage(message: ChatMessageContent): Promise<any> {
    const allowedRoles = [AuthorRole.USER, AuthorRole.ASSISTANT]

    if (!allowedRoles.includes(message.role as any) && message.role !== AuthorRole.TOOL) {
      throw new Error(`Invalid message role '${message.role}'. Allowed roles are ${allowedRoles.join(', ')}.`)
    }

    // Convert message content to OpenAI format
    const messageContents = this.getMessageContents(message)

    return await this.client.beta.threads.messages.create(this.threadId, {
      role: message.role === AuthorRole.TOOL ? 'assistant' : message.role.toLowerCase(),
      content: messageContents,
    })
  }

  /**
   * Get message contents in OpenAI format.
   *
   * @private
   */
  private getMessageContents(message: ChatMessageContent): any[] {
    const contents: any[] = []

    // Process items if they exist
    if (message.items && message.items.length > 0) {
      for (const item of message.items) {
        if (item instanceof TextContent) {
          // Make sure text is a string
          let finalText: string = item.text
          if (typeof finalText !== 'string') {
            if (Array.isArray(finalText)) {
              finalText = (finalText as any[]).map(String).join(' ')
            } else {
              finalText = String(finalText)
            }
          }
          contents.push({
            type: 'text',
            text: finalText,
          })
        } else if (item instanceof ImageContent) {
          if (item.uri) {
            contents.push(item.toDict())
          }
        } else if (item instanceof FileReferenceContent) {
          contents.push({
            type: 'image_file',
            image_file: { file_id: item.fileId },
          })
        }
        // Add more content type handling as needed
      }
    }

    return contents
  }

  /**
   * Generate message content from a thread message.
   *
   * @private
   */
  private generateMessageContent(assistantName: string | null, message: any): ChatMessageContent | null {
    const items: (TextContent | FileReferenceContent)[] = []
    let textContent = ''

    // Process message content blocks
    if (message.content && Array.isArray(message.content)) {
      for (const block of message.content) {
        if (block.type === 'text' && block.text?.value) {
          textContent += block.text.value
          items.push(
            new TextContent({
              text: block.text.value,
            })
          )
        } else if (block.type === 'image_file' && block.image_file?.file_id) {
          items.push(
            new FileReferenceContent({
              fileId: block.image_file.file_id,
            })
          )
        }
        // Add more content type handling as needed
      }
    }

    if (items.length === 0) {
      return null
    }

    return new ChatMessageContent({
      role: message.role === 'user' ? AuthorRole.USER : AuthorRole.ASSISTANT,
      content: textContent,
      name: assistantName || undefined,
      items,
      metadata: {
        thread_id: this.threadId,
        message_id: message.id,
        assistant_id: message.assistant_id,
      },
    })
  }
}
