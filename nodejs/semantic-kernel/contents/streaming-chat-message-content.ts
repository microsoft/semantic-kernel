import { createDefaultLogger } from '../utils/logger'
import { AudioContent } from './audio-content'
import { BinaryContent } from './binary-content'
import { ChatMessageContent, CMCItemTypes } from './chat-message-content'
import { FunctionCallContent } from './function-call-content'
import { FunctionResultContent } from './function-result-content'
import { ImageContent } from './image-content'
import { StreamingAnnotationContent } from './streaming-annotation-content'
import { StreamingFileReferenceContent } from './streaming-file-reference-content'
import { StreamingTextContent } from './streaming-text-content'
import { AuthorRole } from './utils/author-role'
import { FinishReason } from './utils/finish-reason'

const logger = createDefaultLogger('StreamingChatMessageContent')

export type StreamingCMCItemTypes =
  | BinaryContent
  | AudioContent
  | ImageContent
  | FunctionResultContent
  | FunctionCallContent
  | StreamingTextContent
  | StreamingAnnotationContent
  | StreamingFileReferenceContent

/**
 * This is the class for streaming chat message response content.
 *
 * All Chat Completion Services should return an instance of this class as streaming response,
 * where each part of the response as it is streamed is converted to an instance of this class,
 * the end-user will have to either do something directly or gather them and combine them into a
 * new instance. A service can implement their own subclass of this class and return instances of that.
 */
export class StreamingChatMessageContent extends ChatMessageContent {
  choiceIndex: number
  functionInvokeAttempt?: number

  constructor(options: {
    role: AuthorRole
    choiceIndex: number
    items?: StreamingCMCItemTypes[]
    content?: string
    name?: string
    encoding?: string
    finishReason?: FinishReason
    functionInvokeAttempt?: number
    innerContent?: any
    aiModelId?: string
    metadata?: Record<string, any>
  }) {
    const {
      role,
      choiceIndex,
      items,
      content,
      name,
      encoding,
      finishReason,
      functionInvokeAttempt,
      innerContent,
      aiModelId,
      metadata,
    } = options

    const finalItems = items ? [...items] : []

    // If content is provided, create a StreamingTextContent item
    if (content) {
      const textItem = new StreamingTextContent({
        choiceIndex,
        text: content,
        encoding,
        aiModelId,
        innerContent,
        metadata: metadata || {},
      })
      finalItems.push(textItem)
    }

    super({
      role,
      items: finalItems as CMCItemTypes[],
      name,
      encoding,
      finishReason,
      innerContent,
      aiModelId,
      metadata,
    })

    this.choiceIndex = choiceIndex
    this.functionInvokeAttempt = functionInvokeAttempt ?? 0
  }

  /**
   * Return the content of the response encoded in the encoding.
   */
  toBytes(): Buffer {
    return this.content ? Buffer.from(this.content, (this.encoding as BufferEncoding) || 'utf-8') : Buffer.alloc(0)
  }

  /**
   * When combining two StreamingChatMessageContent instances, the content fields are combined.
   *
   * The addition should follow these rules:
   * 1. The inner_content of the two will be combined. If they are not lists, they will be converted to lists.
   * 2. ai_model_id should be the same.
   * 3. encoding should be the same.
   * 4. role should be the same.
   * 5. choice_index should be the same.
   * 6. Metadata will be combined
   */
  add(other: StreamingChatMessageContent): StreamingChatMessageContent {
    if (!(other instanceof StreamingChatMessageContent)) {
      throw new Error(`Cannot add other type to StreamingChatMessageContent, type supplied: ${typeof other}`)
    }
    if (this.choiceIndex !== other.choiceIndex) {
      throw new Error('Cannot add StreamingChatMessageContent with different choice_index')
    }
    if (this.aiModelId !== other.aiModelId) {
      throw new Error('Cannot add StreamingChatMessageContent from different ai_model_id')
    }
    if (this.encoding !== other.encoding) {
      throw new Error('Cannot add StreamingChatMessageContent with different encoding')
    }
    if (this.role && other.role && this.role !== other.role) {
      throw new Error('Cannot add StreamingChatMessageContent with different role')
    }

    return new StreamingChatMessageContent({
      role: this.role,
      items: this.mergeItemsLists(other.items as StreamingCMCItemTypes[]),
      choiceIndex: this.choiceIndex,
      innerContent: this.mergeInnerContents(other.innerContent),
      aiModelId: this.aiModelId,
      metadata: { ...this.metadata, ...other.metadata },
      encoding: this.encoding,
      finishReason: this.finishReason || other.finishReason,
      functionInvokeAttempt: this.functionInvokeAttempt,
      name: this.name || other.name,
    })
  }

  /**
   * Convert to XML element.
   */
  override toElement(): { tag: string; attributes: Record<string, string>; children: any[] } {
    const element = super.toElement()

    // Add choice_index attribute
    if (this.choiceIndex !== undefined) {
      element.attributes.choice_index = String(this.choiceIndex)
    }

    return element
  }

  /**
   * Create a new list with the items of the current instance and the given list.
   */
  private mergeItemsLists(otherItems: StreamingCMCItemTypes[]): StreamingCMCItemTypes[] {
    const newItemsList = [...this.items] as StreamingCMCItemTypes[]

    if (newItemsList.length > 0 || otherItems.length > 0) {
      for (const otherItem of otherItems) {
        let added = false
        for (let id = 0; id < newItemsList.length; id++) {
          const item = newItemsList[id]
          if (item.constructor === otherItem.constructor && 'add' in item && typeof (item as any).add === 'function') {
            try {
              const newItem = (item as any).add(otherItem)
              newItemsList[id] = newItem
              added = true
              break
            } catch (ex) {
              logger.debug(`Could not add item ${otherItem} to ${item}.`, ex)
              continue
            }
          }
        }
        if (!added) {
          logger.debug(`Could not add item ${otherItem} to any item in the list. Adding it as a new item.`)
          newItemsList.push(otherItem)
        }
      }
    }

    return newItemsList
  }

  /**
   * Create a new list with the inner content of the current instance and the given one.
   */
  private mergeInnerContents(otherInnerContent: any): any[] {
    const newInnerContents = Array.isArray(this.innerContent)
      ? [...this.innerContent]
      : this.innerContent
        ? [this.innerContent]
        : []

    const otherContents = Array.isArray(otherInnerContent)
      ? otherInnerContent
      : otherInnerContent
        ? [otherInnerContent]
        : []

    return [...newInnerContents, ...otherContents]
  }
}
