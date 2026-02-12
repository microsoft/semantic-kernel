import { promises as fs } from 'fs'
import { createDefaultLogger } from '../utils/logger'
import { ChatMessageContent } from './chat-message-content'
import { ContentInitializationError, ContentSerializationError } from './exceptions'
import { KernelContent } from './kernel-content'
import { AuthorRole } from './utils/author-role'

const logger = createDefaultLogger('ChatHistory')

const CHAT_HISTORY_TAG = 'chat_history'
const CHAT_MESSAGE_CONTENT_TAG = 'message'

/**
 * Represents a chat history containing a sequence of chat messages.
 */
export class ChatHistory {
  /** The messages in the chat history */
  public messages: ChatMessageContent[] = []

  /** The optional system message */
  public systemMessage?: string

  /**
   * Creates a new ChatHistory instance.
   * @param messages - The messages to initialize the history with
   * @param systemMessage - An optional system message
   */
  constructor(messages: ChatMessageContent[] = [], systemMessage?: string) {
    this.messages = [...messages]
    this.systemMessage = systemMessage

    // If system_message is provided, prepend it to messages
    if (this.systemMessage) {
      this.messages.unshift(
        new ChatMessageContent({
          role: AuthorRole.SYSTEM,
          content: this.systemMessage,
        })
      )
    }
  }

  /**
   * Adds a system message to the chat history.
   * @param content - The message content as string or KernelContent items
   */
  public addSystemMessage(content: string | KernelContent[]): void {
    if (typeof content === 'string') {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.SYSTEM,
          content,
        })
      )
    } else {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.SYSTEM,
          items: content as any,
        })
      )
    }
  }

  /**
   * Adds a developer message to the chat history.
   * @param content - The message content as string or KernelContent items
   */
  public addDeveloperMessage(content: string | KernelContent[]): void {
    if (typeof content === 'string') {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.ASSISTANT,
          content,
        })
      )
    } else {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.ASSISTANT,
          items: content as any,
        })
      )
    }
  }

  /**
   * Adds a user message to the chat history.
   * @param content - The message content as string or KernelContent items
   */
  public addUserMessage(content: string | KernelContent[]): void {
    if (typeof content === 'string') {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.USER,
          content,
        })
      )
    } else {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.USER,
          items: content as any,
        })
      )
    }
  }

  /**
   * Adds an assistant message to the chat history.
   * @param content - The message content as string or KernelContent items
   */
  public addAssistantMessage(content: string | KernelContent[]): void {
    if (typeof content === 'string') {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.ASSISTANT,
          content,
        })
      )
    } else {
      this.addMessage(
        new ChatMessageContent({
          role: AuthorRole.ASSISTANT,
          items: content as any,
        })
      )
    }
  }

  /**
   * Adds a tool message to the chat history.
   * @param content - The message content as string or KernelContent items
   * @param toolCallId - The ID of the tool call this message responds to
   */
  public addToolMessage(content: string | KernelContent[], toolCallId: string): void {
    let message: ChatMessageContent
    if (typeof content === 'string') {
      message = new ChatMessageContent({
        role: AuthorRole.TOOL,
        content,
      })
    } else {
      message = new ChatMessageContent({
        role: AuthorRole.TOOL,
        items: content as any,
      })
    }
    message.metadata = { tool_call_id: toolCallId }
    this.addMessage(message)
  }

  /**
   * Adds a ChatMessageContent instance to the chat history.
   * @param message - The message to add
   */
  public addMessage(message: ChatMessageContent): void {
    this.messages.push(message)
  }

  /**
   * Removes a message from the chat history.
   * @param message - The message to remove
   * @returns true if the message was removed, false otherwise
   */
  public removeMessage(message: ChatMessageContent): boolean {
    const index = this.messages.indexOf(message)
    if (index !== -1) {
      this.messages.splice(index, 1)
      return true
    }
    return false
  }

  /**
   * Gets the number of messages in the chat history.
   */
  public get length(): number {
    return this.messages.length
  }

  /**
   * Gets a message at a specific index.
   * @param index - The index of the message
   * @returns The message at the specified index
   */
  public getItem(index: number): ChatMessageContent | undefined {
    if (index < 0) {
      index = this.messages.length + index
    }
    return this.messages[index]
  }

  /**
   * Checks if a message exists in the chat history.
   * @param message - The message to check for
   * @returns true if the message exists, false otherwise
   */
  public contains(message: ChatMessageContent): boolean {
    return this.messages.includes(message)
  }

  /**
   * Returns a string representation of the chat history.
   */
  public toString(): string {
    return this.toPrompt()
  }

  /**
   * Clears all messages from the chat history.
   */
  public clear(): void {
    this.messages = []
  }

  /**
   * Extends the chat history with multiple messages.
   * @param messages - The messages to add
   */
  public extend(messages: Iterable<ChatMessageContent>): void {
    for (const message of messages) {
      this.addMessage(message)
    }
  }

  /**
   * Replaces the chat history with a new list of messages.
   * @param messages - The messages to replace the history with
   */
  public replace(messages: Iterable<ChatMessageContent>): void {
    this.clear()
    this.extend(messages)
  }

  /**
   * Converts the chat history to a prompt string in XML format.
   * @returns The XML representation of the chat history
   */
  public toPrompt(): string {
    const elements = this.messages.map((msg) => msg.toElement())
    const chatHistoryXml = `<${CHAT_HISTORY_TAG}>${elements.join('')}</${CHAT_HISTORY_TAG}>`
    return chatHistoryXml
  }

  /**
   * Returns an iterator over the messages in the history.
   */
  public *[Symbol.iterator](): Generator<ChatMessageContent, void, unknown> {
    yield* this.messages
  }

  /**
   * Checks if two ChatHistory instances are equal.
   * @param other - The other ChatHistory to compare with
   * @returns true if the histories are equal, false otherwise
   */
  public equals(other: any): boolean {
    if (!(other instanceof ChatHistory)) {
      return false
    }

    if (this.messages.length !== other.messages.length) {
      return false
    }

    // Simple comparison - check if messages have the same role and content
    return this.messages.every((msg, idx) => {
      const otherMsg = other.messages[idx]
      return msg.role === otherMsg.role && msg.content === otherMsg.content
    })
  }

  /**
   * Creates a ChatHistory instance from a rendered prompt.
   * @param renderedPrompt - The rendered prompt to parse
   * @returns A new ChatHistory instance
   */
  public static fromRenderedPrompt(renderedPrompt: string): ChatHistory {
    const messages: ChatMessageContent[] = []
    const prompt = renderedPrompt.trim()

    // Try to parse as XML
    try {
      // Simple XML parsing - in production, use a proper XML parser
      const messageRegex = new RegExp(
        `<${CHAT_MESSAGE_CONTENT_TAG}[^>]*>([\\s\\S]*?)</${CHAT_MESSAGE_CONTENT_TAG}>`,
        'g'
      )
      const matches = prompt.matchAll(messageRegex)

      let hasMatches = false
      for (const match of matches) {
        hasMatches = true
        // fromElement expects an object, not a string
        // For now, just create a simple user message
        messages.push(
          new ChatMessageContent({
            role: AuthorRole.USER,
            content: match[1] || match[0],
          })
        )
      }

      if (!hasMatches) {
        // No messages found, treat as plain user message
        return new ChatHistory([
          new ChatMessageContent({
            role: AuthorRole.USER,
            content: this.unescapeXml(prompt),
          }),
        ])
      }

      // If only one system message, convert to user
      if (messages.length === 1 && messages[0].role === AuthorRole.SYSTEM) {
        messages[0].role = AuthorRole.USER
      }

      return new ChatHistory(messages)
    } catch (error) {
      logger.error('Failed to parse rendered prompt as XML:', error)
      // Failed to parse, treat as plain text user message
      return new ChatHistory([
        new ChatMessageContent({
          role: AuthorRole.USER,
          content: this.unescapeXml(prompt),
        }),
      ])
    }
  }

  /**
   * Unescapes XML entities.
   * @param str - The string to unescape
   * @returns The unescaped string
   */
  private static unescapeXml(str: string): string {
    return str
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#039;/g, "'")
  }

  /**
   * Serializes the ChatHistory to a JSON string.
   * @returns The JSON string representation
   */
  public serialize(): string {
    try {
      return JSON.stringify(
        {
          messages: this.messages.map((msg) => msg.toDict()),
          systemMessage: this.systemMessage,
        },
        null,
        2
      )
    } catch (error) {
      throw new ContentSerializationError(`Unable to serialize ChatHistory to JSON: ${error}`)
    }
  }

  /**
   * Restores a ChatHistory from a JSON string.
   * @param chatHistoryJson - The JSON string to deserialize
   * @returns The restored ChatHistory instance
   */
  public static restoreChatHistory(chatHistoryJson: string): ChatHistory {
    try {
      const data = JSON.parse(chatHistoryJson)
      // Simple restoration - create messages from role and content
      const messages =
        data.messages?.map(
          (msgData: any) =>
            new ChatMessageContent({
              role: msgData.role,
              content: msgData.content,
              name: msgData.name,
              items: msgData.items,
            })
        ) || []
      return new ChatHistory(messages, data.systemMessage)
    } catch (error) {
      throw new ContentInitializationError(`Invalid JSON format: ${error}`)
    }
  }

  /**
   * Stores the serialized ChatHistory to a file.
   * @param filePath - The path to the file to write
   */
  public async storeChatHistoryToFile(filePath: string): Promise<void> {
    const jsonStr = this.serialize()
    await fs.writeFile(filePath, jsonStr, 'utf-8')
  }

  /**
   * Loads a ChatHistory from a file.
   * @param filePath - The path to the file to read
   * @returns The loaded ChatHistory instance
   */
  public static async loadChatHistoryFromFile(filePath: string): Promise<ChatHistory> {
    const jsonStr = await fs.readFile(filePath, 'utf-8')
    return this.restoreChatHistory(jsonStr)
  }
}
