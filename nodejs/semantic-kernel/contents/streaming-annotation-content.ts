import { CitationType } from './annotation-content'
import { STREAMING_ANNOTATION_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'

/**
 * Streaming Annotation content.
 */
export class StreamingAnnotationContent extends KernelContent {
  readonly contentType: string = STREAMING_ANNOTATION_CONTENT_TAG
  readonly tag: string = STREAMING_ANNOTATION_CONTENT_TAG
  fileId?: string
  quote?: string
  startIndex?: number
  endIndex?: number
  url?: string
  title?: string
  citationType?: CitationType

  constructor(
    options: {
      fileId?: string
      quote?: string
      startIndex?: number
      endIndex?: number
      url?: string
      title?: string
      citationType?: CitationType
      type?: CitationType // Alias for citationType
      innerContent?: any
      aiModelId?: string
      metadata?: Record<string, any>
    } = {}
  ) {
    const { fileId, quote, startIndex, endIndex, url, title, citationType, type, innerContent, aiModelId, metadata } =
      options
    super({ innerContent, aiModelId, metadata })
    this.fileId = fileId
    this.quote = quote
    this.startIndex = startIndex
    this.endIndex = endIndex
    this.url = url
    this.title = title
    // Support both citationType and type (alias)
    this.citationType = citationType ?? type
  }

  /**
   * Return the string representation of the annotation content.
   */
  toString(): string {
    const ctype = this.citationType
    return `StreamingAnnotationContent(type=${ctype}, file_id=${this.fileId}, url=${this.url}, quote=${this.quote}, title=${this.title}, start_index=${this.startIndex}, end_index=${this.endIndex})`
  }

  /**
   * Convert the annotation content to an element.
   */
  toElement(): { tag: string; attributes: Record<string, string> } {
    const element: { tag: string; attributes: Record<string, string> } = {
      tag: this.tag,
      attributes: {},
    }

    if (this.citationType !== undefined) {
      element.attributes.type = String(this.citationType)
    }
    if (this.fileId) {
      element.attributes.file_id = this.fileId
    }
    if (this.quote) {
      element.attributes.quote = this.quote
    }
    if (this.startIndex !== undefined) {
      element.attributes.start_index = String(this.startIndex)
    }
    if (this.endIndex !== undefined) {
      element.attributes.end_index = String(this.endIndex)
    }
    if (this.url !== undefined) {
      element.attributes.url = this.url
    }
    if (this.title !== undefined) {
      element.attributes.title = this.title
    }

    return element
  }

  /**
   * Create an instance from an element.
   */
  static fromElement(element: { tag: string; attributes: Record<string, string> }): StreamingAnnotationContent {
    return new StreamingAnnotationContent({
      type: element.attributes.type as CitationType | undefined,
      fileId: element.attributes.file_id,
      quote: element.attributes.quote,
      startIndex: element.attributes.start_index ? parseInt(element.attributes.start_index, 10) : undefined,
      endIndex: element.attributes.end_index ? parseInt(element.attributes.end_index, 10) : undefined,
      url: element.attributes.url || undefined,
      title: element.attributes.title || undefined,
    })
  }

  /**
   * Convert the instance to a dictionary.
   */
  toDict(): Record<string, any> {
    const ctype = this.citationType
    return {
      type: 'text',
      text: `type=${ctype}, ${this.fileId || this.url}, quote=${this.quote}, title=${this.title} (Start Index=${this.startIndex}->End Index=${this.endIndex})`,
    }
  }
}
