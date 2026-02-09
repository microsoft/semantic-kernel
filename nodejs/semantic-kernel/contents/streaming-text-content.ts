import { TextContent } from './text-content'

/**
 * This represents streaming text response content.
 */
export class StreamingTextContent extends TextContent {
  choiceIndex: number

  constructor(options: {
    choiceIndex: number
    text: string
    encoding?: string
    innerContent?: any
    aiModelId?: string
    metadata?: Record<string, any>
  }) {
    const { choiceIndex, text, encoding, innerContent, aiModelId, metadata } = options
    super({ text, encoding, innerContent, aiModelId, metadata })
    this.choiceIndex = choiceIndex
  }

  /**
   * Return the content of the response encoded in the encoding.
   */
  toBytes(): Buffer {
    return this.text ? Buffer.from(this.text, (this.encoding as BufferEncoding) || 'utf-8') : Buffer.alloc(0)
  }

  /**
   * When combining two StreamingTextContent instances, the text fields are combined.
   *
   * The addition should follow these rules:
   * 1. The inner_content of the two will be combined. If they are not lists, they will be converted to lists.
   * 2. ai_model_id should be the same.
   * 3. encoding should be the same.
   * 4. choice_index should be the same.
   * 5. Metadata will be combined.
   */
  add(other: TextContent): StreamingTextContent {
    if (other instanceof StreamingTextContent && this.choiceIndex !== other.choiceIndex) {
      throw new Error('Cannot add StreamingTextContent with different choice_index')
    }
    if (this.aiModelId !== other.aiModelId) {
      throw new Error('Cannot add StreamingTextContent from different ai_model_id')
    }
    if (this.encoding !== other.encoding) {
      throw new Error('Cannot add StreamingTextContent with different encoding')
    }

    return new StreamingTextContent({
      choiceIndex: this.choiceIndex,
      innerContent: this.mergeInnerContents(other.innerContent),
      aiModelId: this.aiModelId,
      metadata: this.metadata,
      text: (this.text || '') + (other.text || ''),
      encoding: this.encoding,
    })
  }

  /**
   * Merge inner contents into a list.
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
