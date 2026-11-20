/**
 * Base class for all kernel contents.
 *
 * This abstract class provides the foundation for all content types
 * in the Semantic Kernel, including text, images, annotations, and
 * other content types.
 */
export abstract class KernelContent {
  /**
   * Inner content object from the underlying service.
   * Note: This is excluded from serialization. If you need to preserve
   * the inner content, save it separately before serializing.
   */
  innerContent?: any

  /**
   * The AI model ID that generated this content.
   */
  aiModelId?: string

  /**
   * Additional metadata associated with this content.
   */
  metadata: Record<string, any>

  /**
   * Create a KernelContent instance.
   *
   * @param options - Configuration options
   * @param options.innerContent - Inner content from the service (excluded from serialization)
   * @param options.aiModelId - The AI model ID
   * @param options.metadata - Additional metadata
   */
  constructor(options?: { innerContent?: any; aiModelId?: string; metadata?: Record<string, any> }) {
    this.innerContent = options?.innerContent
    this.aiModelId = options?.aiModelId
    this.metadata = options?.metadata || {}
  }

  /**
   * Return the string representation of the content.
   */
  abstract toString(): string

  /**
   * Convert the instance to an element representation.
   */
  abstract toElement(): any

  /**
   * Create an instance from an element representation.
   *
   * @param element - The element to create from
   */
  static fromElement(_element: any): KernelContent {
    throw new Error('fromElement must be implemented by subclass')
  }

  /**
   * Convert the instance to a dictionary/object.
   */
  abstract toDict(): Record<string, any>

  /**
   * Convert to JSON representation.
   * By default, excludes innerContent from serialization.
   */
  toJSON(): Record<string, any> {
    const result: Record<string, any> = {
      metadata: this.metadata,
    }

    if (this.aiModelId) {
      result.aiModelId = this.aiModelId
    }

    // innerContent is intentionally excluded from serialization
    // as per Python implementation

    return result
  }
}
