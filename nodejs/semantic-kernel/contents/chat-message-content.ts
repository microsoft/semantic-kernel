import { createDefaultLogger } from '../utils/logger'
import { AnnotationContent } from './annotation-content'
import { AudioContent } from './audio-content'
import { BinaryContent } from './binary-content'
import { CHAT_MESSAGE_CONTENT_TAG, TAG_CONTENT_MAP } from './const'
import { FileReferenceContent } from './file-reference-content'
import { FunctionCallContent } from './function-call-content'
import { FunctionResultContent } from './function-result-content'
import { ImageContent } from './image-content'
import { KernelContent } from './kernel-content'
import { ReasoningContent } from './reasoning-content'
import { StreamingAnnotationContent } from './streaming-annotation-content'
import { StreamingFileReferenceContent } from './streaming-file-reference-content'
import { TextContent } from './text-content'
import { AuthorRole } from './utils/author-role'
import { FinishReason } from './utils/finish-reason'
import { Status } from './utils/status'

const logger = createDefaultLogger('ChatMessageContent')

export type CMCItemTypes =
  | AnnotationContent
  | BinaryContent
  | ImageContent
  | TextContent
  | FunctionResultContent
  | FunctionCallContent
  | FileReferenceContent
  | ReasoningContent
  | StreamingAnnotationContent
  | StreamingFileReferenceContent
  | AudioContent

/**
 * This is the class for chat message response content.
 *
 * All Chat Completion Services should return an instance of this class as response.
 * Or they can implement their own subclass of this class and return an instance.
 */
export class ChatMessageContent extends KernelContent {
  readonly contentType: string = CHAT_MESSAGE_CONTENT_TAG
  readonly tag: string = CHAT_MESSAGE_CONTENT_TAG
  role: AuthorRole
  name?: string
  items: CMCItemTypes[]
  encoding?: string
  finishReason?: FinishReason
  status?: Status

  constructor(options: {
    role: AuthorRole
    items?: CMCItemTypes[]
    content?: string
    name?: string
    encoding?: string
    finishReason?: FinishReason
    status?: Status
    innerContent?: any
    aiModelId?: string
    metadata?: Record<string, any>
  }) {
    const { role, items, content, name, encoding, finishReason, status, innerContent, aiModelId, metadata } = options

    super({ innerContent, aiModelId, metadata })
    this.role = role
    this.name = name
    this.encoding = encoding
    this.finishReason = finishReason
    this.status = status

    const finalItems = items ? [...items] : []

    // If content is provided, create a TextContent item
    if (content) {
      const textItem = new TextContent({
        text: content,
        encoding,
        aiModelId,
        innerContent,
        metadata: metadata || {},
      })
      finalItems.push(textItem)
    }

    this.items = finalItems
  }

  /**
   * Get the content of the response, will find the first TextContent's text.
   */
  get content(): string {
    for (const item of this.items) {
      if (item instanceof TextContent) {
        return item.text
      }
    }
    return ''
  }

  /**
   * Set the content of the response.
   */
  set content(value: string) {
    if (!value) {
      logger.warn(
        'Setting empty content on ChatMessageContent does not work, ' +
          'you can do this through the underlying items if needed, ignoring.'
      )
      return
    }

    // Find existing TextContent and update it
    for (const item of this.items) {
      if (item instanceof TextContent) {
        item.text = value
        item.encoding = this.encoding
        return
      }
    }

    // If no TextContent found, create a new one
    this.items.push(
      new TextContent({
        text: value,
        encoding: this.encoding,
        aiModelId: this.aiModelId,
        innerContent: this.innerContent,
        metadata: this.metadata,
      })
    )
  }

  /**
   * Get the content of the response as a string.
   */
  toString(): string {
    return this.content || ''
  }

  /**
   * Convert the ChatMessageContent to an XML Element.
   */
  toElement(): { tag: string; attributes: Record<string, string>; children: any[] } {
    const element: { tag: string; attributes: Record<string, string>; children: any[] } = {
      tag: this.tag,
      attributes: {},
      children: [],
    }

    // Add attributes for specific fields
    const fields = ['role', 'name', 'encoding', 'finishReason', 'aiModelId']
    for (const field of fields) {
      const value = (this as any)[field]
      if (value !== undefined && value !== null) {
        element.attributes[field] = typeof value === 'object' && 'value' in value ? value.value : String(value)
      }
    }

    // Add items as children
    for (const item of this.items) {
      element.children.push(item.toElement())
    }

    return element
  }

  /**
   * Create a new instance of ChatMessageContent from an XML element.
   */
  static fromElement(element: {
    tag: string
    attributes: Record<string, string>
    text?: string
    children?: any[]
  }): ChatMessageContent {
    if (element.tag !== CHAT_MESSAGE_CONTENT_TAG) {
      throw new Error(`Element tag is not ${CHAT_MESSAGE_CONTENT_TAG}`)
    }

    const kwargs: Record<string, any> = { ...element.attributes }
    const items: KernelContent[] = []

    // Handle text content
    if (element.text) {
      items.push(new TextContent({ text: this.unescapeHtml(element.text) }))
    }

    // Handle children
    if (element.children) {
      for (const child of element.children) {
        if (child.tag && TAG_CONTENT_MAP[child.tag]) {
          items.push(TAG_CONTENT_MAP[child.tag].fromElement(child))
        } else {
          logger.warn(`Unknown tag "${child.tag}" in ChatMessageContent, treating as text`)
          items.push(new TextContent({ text: String(child) }))
        }
      }
    }

    // Handle content vs items
    if (items.length === 1 && items[0] instanceof TextContent) {
      kwargs.content = items[0].text
    } else if (items.every((item) => item instanceof TextContent)) {
      kwargs.content = items.map((item) => (item as TextContent).text).join('')
    } else {
      kwargs.items = items
    }

    // Remove choice_index if present (for StreamingChatMessageContent)
    if ('choice_index' in kwargs) {
      logger.info(
        'Seems like you are trying to create a StreamingChatMessageContent, ' +
          'use StreamingChatMessageContent.fromElement instead, ignoring that field ' +
          'and creating a ChatMessageContent instance.'
      )
      delete kwargs.choice_index
    }

    return new ChatMessageContent(kwargs as any)
  }

  /**
   * Convert the ChatMessageContent to a prompt.
   */
  toPrompt(): string {
    const element = this.toElement()
    // Simple XML serialization
    return this.serializeElement(element)
  }

  /**
   * Serialize the ChatMessageContent to a dictionary.
   */
  toDict(roleKey: string = 'role', contentKey: string = 'content'): Record<string, any> {
    const ret: Record<string, any> = {
      [roleKey]: this.role,
    }

    if (this.role === AuthorRole.ASSISTANT && this.items.some((item) => item instanceof FunctionCallContent)) {
      ret.tool_calls = this.items.filter((item) => item instanceof FunctionCallContent).map((item) => item.toDict())
    } else {
      ret[contentKey] = this.parseItems()
    }

    if (this.role === AuthorRole.TOOL) {
      const firstItem = this.items[0]
      if (firstItem instanceof FunctionResultContent) {
        ret.tool_call_id = firstItem.id || ''
      }
    }

    if (this.role !== AuthorRole.TOOL && this.name) {
      ret.name = this.name
    }

    return ret
  }

  /**
   * Parse the items of the ChatMessageContent.
   */
  private parseItems(): string | Record<string, any>[] {
    if (this.items.length === 1 && this.items[0] instanceof TextContent) {
      return this.items[0].text
    }
    if (this.items.length === 1 && this.items[0] instanceof FunctionResultContent) {
      return String(this.items[0].result)
    }
    return this.items.map((item) => item.toDict())
  }

  /**
   * Simple element serialization helper.
   */
  private serializeElement(element: { tag: string; attributes: Record<string, string>; children?: any[] }): string {
    let result = `<${element.tag}`
    for (const [key, value] of Object.entries(element.attributes)) {
      result += ` ${key}="${this.escapeXml(value)}"`
    }
    if (element.children && element.children.length > 0) {
      result += '>'
      for (const child of element.children) {
        result += this.serializeElement(child)
      }
      result += `</${element.tag}>`
    } else {
      result += '/>'
    }
    return result
  }

  /**
   * Escape XML special characters.
   */
  private escapeXml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
  }

  /**
   * Unescape HTML entities.
   */
  private static unescapeHtml(text: string): string {
    const htmlEntities: Record<string, string> = {
      '&amp;': '&',
      '&lt;': '<',
      '&gt;': '>',
      '&quot;': '"',
      '&#39;': "'",
      '&nbsp;': ' ',
    }

    return text.replace(/&[^;]+;/g, (entity) => htmlEntities[entity] || entity)
  }
}
