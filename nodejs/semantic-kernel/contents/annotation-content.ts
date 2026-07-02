import { ANNOTATION_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'

/**
 * Citation type enumeration.
 */
export enum CitationType {
  URL_CITATION = 'url_citation',
  FILE_PATH = 'file_path',
  FILE_CITATION = 'file_citation',
  CONTAINER_FILE_CITATION = 'container_file_citation',
}

/**
 * Annotation content class.
 *
 * Represents annotation metadata for citations, file references, and other
 * annotated content in chat messages.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
export class AnnotationContent extends KernelContent {
  readonly contentType: string = ANNOTATION_CONTENT_TAG
  readonly tag: string = ANNOTATION_CONTENT_TAG

  fileId?: string
  quote?: string
  startIndex?: number
  endIndex?: number
  url?: string
  title?: string
  citationType?: CitationType
  containerId?: string
  filename?: string

  /**
   * Create an AnnotationContent instance.
   *
   * @param options - Configuration options
   * @param options.type - The citation type (alias for citationType)
   * @param options.citationType - The citation type
   * @param options.fileId - The file ID for file citations
   * @param options.quote - The quoted text from the citation
   * @param options.startIndex - The start index of the annotation in the text
   * @param options.endIndex - The end index of the annotation in the text
   * @param options.url - The URL for URL citations
   * @param options.title - The title of the citation
   * @param options.containerId - The container ID for container file citations
   * @param options.filename - The filename for file citations
   * @param options.innerContent - Inner content from the service
   * @param options.aiModelId - The AI model ID
   * @param options.metadata - Additional metadata
   */
  constructor(options?: {
    type?: CitationType | string
    citationType?: CitationType
    fileId?: string
    quote?: string
    startIndex?: number
    endIndex?: number
    url?: string
    title?: string
    containerId?: string
    filename?: string
    innerContent?: any
    aiModelId?: string
    metadata?: Record<string, any>
  }) {
    super({
      innerContent: options?.innerContent,
      aiModelId: options?.aiModelId,
      metadata: options?.metadata,
    })

    if (options) {
      // Support both 'type' and 'citationType' (type is alias)
      if (options.type && !options.citationType) {
        this.citationType = this.parseCitationType(options.type)
      } else if (options.citationType) {
        this.citationType = options.citationType
      }

      this.fileId = options.fileId
      this.quote = options.quote
      this.startIndex = options.startIndex
      this.endIndex = options.endIndex
      this.url = options.url
      this.title = options.title
      this.containerId = options.containerId
      this.filename = options.filename
    }
  }

  /**
   * Parse citation type from string.
   *
   * @private
   */
  private parseCitationType(type: string | CitationType): CitationType | undefined {
    if (typeof type === 'string') {
      const normalizedType = type.toLowerCase()
      for (const [_key, value] of Object.entries(CitationType)) {
        if (value === normalizedType) {
          return value as CitationType
        }
      }
      return undefined
    }
    return type
  }

  /**
   * Get string representation of the annotation content.
   */
  toString(): string {
    const typeStr = this.citationType || 'unknown'
    return `AnnotationContent(type=${typeStr}, file_id=${this.fileId}, url=${this.url}, quote=${this.quote}, start_index=${this.startIndex}, end_index=${this.endIndex})`
  }

  /**
   * Convert the annotation content to an XML element representation.
   *
   * @returns Object with tag and attributes
   */
  toElement(): { tag: string; attributes: Record<string, string> } {
    const attributes: Record<string, string> = {}

    if (this.citationType) {
      attributes.type = this.citationType
    }
    if (this.fileId) {
      attributes.file_id = this.fileId
    }
    if (this.quote) {
      attributes.quote = this.quote
    }
    if (this.startIndex !== undefined) {
      attributes.start_index = String(this.startIndex)
    }
    if (this.endIndex !== undefined) {
      attributes.end_index = String(this.endIndex)
    }
    if (this.url) {
      attributes.url = this.url
    }
    if (this.title) {
      attributes.title = this.title
    }

    return {
      tag: this.tag,
      attributes,
    }
  }

  /**
   * Create an AnnotationContent instance from an element representation.
   *
   * @param element - Element with tag and attributes
   * @returns New AnnotationContent instance
   */
  static fromElement(element: { tag: string; attributes: Record<string, string> }): AnnotationContent {
    return new AnnotationContent({
      type: element.attributes.type,
      fileId: element.attributes.file_id,
      quote: element.attributes.quote,
      startIndex: element.attributes.start_index ? parseInt(element.attributes.start_index, 10) : undefined,
      endIndex: element.attributes.end_index ? parseInt(element.attributes.end_index, 10) : undefined,
      url: element.attributes.url,
      title: element.attributes.title,
    })
  }

  /**
   * Convert the instance to a dictionary/object.
   *
   * @returns Object representation suitable for serialization
   */
  toDict(): { type: string; text: string } {
    const typeStr = this.citationType || 'unknown'
    const location = this.fileId || this.url || ''
    const quoteStr = this.quote || ''
    const indexStr =
      this.startIndex !== undefined && this.endIndex !== undefined
        ? `(Start Index=${this.startIndex}->End Index=${this.endIndex})`
        : ''

    return {
      type: 'text',
      text: `type=${typeStr}, ${location} ${quoteStr} ${indexStr}`.trim(),
    }
  }

  /**
   * Convert to JSON representation.
   */
  toJSON(): Record<string, any> {
    const result = super.toJSON()

    result.contentType = this.contentType
    result.tag = this.tag

    if (this.citationType) result.citationType = this.citationType
    if (this.fileId) result.fileId = this.fileId
    if (this.quote) result.quote = this.quote
    if (this.startIndex !== undefined) result.startIndex = this.startIndex
    if (this.endIndex !== undefined) result.endIndex = this.endIndex
    if (this.url) result.url = this.url
    if (this.title) result.title = this.title
    if (this.containerId) result.containerId = this.containerId
    if (this.filename) result.filename = this.filename

    return result
  }
}
