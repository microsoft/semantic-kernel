import { REASONING_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'

/**
 * Represents reasoning content.
 *
 * Exposes a human-readable reasoning text. Any provider-specific fields (for example: ids, encrypted blobs,
 * statuses, token info) must be carried in metadata on the base KernelContent.
 */
export class ReasoningContent extends KernelContent {
  readonly contentType: string = REASONING_CONTENT_TAG
  readonly tag: string = REASONING_CONTENT_TAG
  text?: string

  constructor(
    options: {
      text?: string
      innerContent?: any
      aiModelId?: string
      metadata?: Record<string, any>
    } = {}
  ) {
    const { text, innerContent, aiModelId, metadata } = options
    super({ innerContent, aiModelId, metadata })
    this.text = text
  }

  /**
   * Return the text of the reasoning content.
   */
  toString(): string {
    return this.text || ''
  }

  /**
   * Convert the instance to an XML Element.
   */
  toElement(): { tag: string; attributes: Record<string, string>; text?: string } {
    return {
      tag: this.tag,
      attributes: {},
      text: this.text,
    }
  }

  /**
   * Create an instance from an XML Element.
   */
  static fromElement(element: { tag: string; attributes: Record<string, string>; text?: string }): ReasoningContent {
    if (element.tag !== REASONING_CONTENT_TAG) {
      throw new Error(`Element tag is not ${REASONING_CONTENT_TAG}`)
    }

    // Unescape HTML entities in the text
    const text = element.text ? this.unescapeHtml(element.text) : ''

    return new ReasoningContent({ text })
  }

  /**
   * Convert the instance to a dictionary suitable for message serialization.
   */
  toDict(): Record<string, any> {
    return {
      type: 'reasoning',
      text: this.text || '',
    }
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
