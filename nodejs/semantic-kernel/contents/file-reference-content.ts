import { FILE_REFERENCE_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'

/**
 * File reference content.
 */
export class FileReferenceContent extends KernelContent {
  readonly contentType: string = FILE_REFERENCE_CONTENT_TAG
  readonly tag: string = FILE_REFERENCE_CONTENT_TAG
  fileId?: string
  tools: any[]
  dataSource?: any

  constructor(
    options: {
      fileId?: string
      tools?: any[]
      dataSource?: any
      innerContent?: any
      aiModelId?: string
      metadata?: Record<string, any>
    } = {}
  ) {
    const { fileId, tools = [], dataSource, innerContent, aiModelId, metadata } = options
    super({ innerContent, aiModelId, metadata })
    this.fileId = fileId
    this.tools = tools
    this.dataSource = dataSource
  }

  /**
   * Return the string representation of the file reference content.
   */
  toString(): string {
    return `FileReferenceContent(file_id=${this.fileId})`
  }

  /**
   * Convert the file reference content to an element.
   */
  toElement(): { tag: string; attributes: Record<string, string> } {
    const element: { tag: string; attributes: Record<string, string> } = {
      tag: this.tag,
      attributes: {},
    }

    if (this.fileId) {
      element.attributes.file_id = this.fileId
    }

    return element
  }

  /**
   * Create an instance from an element.
   */
  static fromElement(element: { tag: string; attributes: Record<string, string> }): FileReferenceContent {
    return new FileReferenceContent({
      fileId: element.attributes.file_id,
    })
  }

  /**
   * Convert the instance to a dictionary.
   */
  toDict(): Record<string, any> {
    return {
      file_id: this.fileId,
    }
  }
}
