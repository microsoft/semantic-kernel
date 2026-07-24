import { TEXT_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'

/**
 * This represents text response content.
 */
export class TextContent extends KernelContent {
  readonly contentType: string = TEXT_CONTENT_TAG
  readonly tag: string = TEXT_CONTENT_TAG
  text: string
  encoding?: string

  constructor(options: {
    text: string
    encoding?: string
    innerContent?: any
    aiModelId?: string
    metadata?: Record<string, any>
  }) {
    const { text, encoding, innerContent, aiModelId, metadata } = options
    super({ innerContent, aiModelId, metadata })
    this.text = text
    this.encoding = encoding
  }

  /**
   * Return the text of the response.
   */
  toString(): string {
    return this.text
  }

  /**
   * Convert the instance to an element.
   */
  toElement(): { tag: string; attributes: Record<string, string>; text?: string } {
    const element: { tag: string; attributes: Record<string, string>; text?: string } = {
      tag: this.tag,
      attributes: {},
      text: this.text,
    }

    if (this.encoding) {
      element.attributes.encoding = this.encoding
    }

    return element
  }

  /**
   * Create an instance from an element.
   */
  static fromElement(element: { tag: string; attributes: Record<string, string>; text?: string }): TextContent {
    if (element.tag !== TEXT_CONTENT_TAG) {
      throw new Error(`Element tag is not ${TEXT_CONTENT_TAG}`)
    }

    // Unescape HTML entities in the text
    const text = element.text ? this.unescapeHtml(element.text) : ''
    const encoding = element.attributes.encoding

    return new TextContent({ text, encoding })
  }

  /**
   * Convert the instance to a dictionary.
   */
  toDict(): Record<string, any> {
    return {
      type: 'text',
      text: this.text,
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
