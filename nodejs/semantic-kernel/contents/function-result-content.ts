import { ChatMessageContent } from './chat-message-content'
import { FUNCTION_RESULT_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'
import type { StreamingChatMessageContent } from './streaming-chat-message-content'
import { TextContent } from './text-content'
import { AuthorRole } from './utils/author-role'

const DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR = '-'

/**
 * This class represents function result content.
 */
export class FunctionResultContent extends KernelContent {
  readonly contentType: string = FUNCTION_RESULT_CONTENT_TAG
  readonly tag: string = FUNCTION_RESULT_CONTENT_TAG
  id?: string
  callId?: string
  result: any
  name?: string
  functionName: string
  pluginName?: string
  encoding?: string

  constructor(
    options: {
      id?: string
      callId?: string
      name?: string
      functionName?: string
      pluginName?: string
      result?: any
      encoding?: string
      innerContent?: any
      aiModelId?: string
      metadata?: Record<string, any>
    } = {}
  ) {
    const { id, callId, result, encoding, innerContent, aiModelId, metadata } = options
    let { name, functionName, pluginName } = options

    // Handle name construction and parsing
    if (functionName && pluginName && !name) {
      name = `${pluginName}${DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR}${functionName}`
    }
    if (name && !functionName && !pluginName) {
      if (name.includes(DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR)) {
        const parts = name.split(DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR)
        pluginName = parts[0]
        functionName = parts.slice(1).join(DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR)
      } else {
        functionName = name
      }
    }

    super({ innerContent, aiModelId, metadata })
    this.id = id
    this.callId = callId
    this.name = name
    this.functionName = functionName || ''
    this.pluginName = pluginName
    this.result = result
    this.encoding = encoding
  }

  /**
   * Return the text of the response.
   */
  toString(): string {
    return String(this.result)
  }

  /**
   * Convert the instance to an element.
   */
  toElement(): { tag: string; attributes: Record<string, string>; text?: string } {
    const element: { tag: string; attributes: Record<string, string>; text?: string } = {
      tag: this.tag,
      attributes: {},
      text: String(this.result),
    }

    if (this.id) {
      element.attributes.id = this.id
    }
    if (this.name) {
      element.attributes.name = this.name
    }

    return element
  }

  /**
   * Create an instance from an element.
   */
  static fromElement(element: {
    tag: string
    attributes: Record<string, string>
    text?: string
  }): FunctionResultContent {
    if (element.tag !== FUNCTION_RESULT_CONTENT_TAG) {
      throw new Error(`Element tag is not ${FUNCTION_RESULT_CONTENT_TAG}`)
    }

    return new FunctionResultContent({
      id: element.attributes.id || '',
      result: element.text,
      name: element.attributes.name,
    })
  }

  /**
   * Create an instance from a FunctionCallContent and a result.
   */
  static fromFunctionCallContentAndResult(
    functionCallContent: any, // FunctionCallContent
    result: any, // FunctionResult | TextContent | ChatMessageContent | any
    metadata?: Record<string, any>
  ): FunctionResultContent {
    metadata = metadata || {}
    metadata = { ...metadata, ...(functionCallContent.metadata || {}) }
    metadata = { ...metadata, ...(result.metadata || {}) }

    const innerContent = result
    let res: any

    // Handle FunctionResult
    if (result && typeof result === 'object' && 'value' in result) {
      res = result.value
    } else if (result instanceof TextContent) {
      res = result.text
    } else if (result && typeof result === 'object' && 'items' in result && Array.isArray(result.items)) {
      // ChatMessageContent
      const firstItem = result.items[0]
      if (firstItem instanceof TextContent) {
        res = firstItem.text
      } else if (firstItem && 'dataUri' in firstItem) {
        // ImageContent
        res = firstItem.dataUri
      } else if (firstItem instanceof FunctionResultContent) {
        res = firstItem.result
      } else {
        res = String(result)
      }
    } else {
      res = result
    }

    return new FunctionResultContent({
      id: functionCallContent.id || 'unknown',
      callId: functionCallContent.callId,
      innerContent,
      result: res,
      functionName: functionCallContent.functionName,
      pluginName: functionCallContent.pluginName,
      aiModelId: functionCallContent.aiModelId,
      metadata,
    })
  }

  /**
   * Convert the instance to a ChatMessageContent.
   */
  toChatMessageContent(): any {
    // Dynamic import to avoid circular dependency
    return new ChatMessageContent({
      role: AuthorRole.TOOL,
      items: [this],
    })
  }

  /**
   * Convert the instance to a StreamingChatMessageContent.
   */
  async toStreamingChatMessageContent(): Promise<StreamingChatMessageContent> {
    const { StreamingChatMessageContent } = await import('./streaming-chat-message-content.js')
    return new StreamingChatMessageContent({
      role: AuthorRole.TOOL,
      choiceIndex: 0,
      items: [this],
    })
  }

  /**
   * Convert the instance to a dictionary.
   */
  toDict(): Record<string, any> {
    return {
      tool_call_id: this.id,
      content: this.result,
    }
  }

  /**
   * Split the name into a plugin and function name.
   * @deprecated Use functionName and pluginName properties instead.
   */
  splitName(): [string, string] {
    return [this.pluginName || '', this.functionName]
  }

  /**
   * Get the fully qualified name of the function with a custom separator.
   */
  customFullyQualifiedName(separator: string): string {
    return this.pluginName ? `${this.pluginName}${separator}${this.functionName}` : this.functionName
  }

  /**
   * Serialize the result to a string.
   */
  serializeResult(value: any): string {
    return String(value)
  }
}
