import { createDefaultLogger } from '../utils/logger'
import { FUNCTION_CALL_CONTENT_TAG } from './const'
import { KernelContent } from './kernel-content'

const DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR = '-'
const EMPTY_VALUES: (string | null | undefined)[] = ['', '{}', null, undefined]

const logger = createDefaultLogger('FunctionCallContent')

/**
 * Class to hold a function call response.
 */
export class FunctionCallContent extends KernelContent {
  readonly contentType: string = FUNCTION_CALL_CONTENT_TAG
  readonly tag: string = FUNCTION_CALL_CONTENT_TAG
  id?: string
  callId?: string
  index?: number
  name?: string
  functionName: string
  pluginName?: string
  arguments?: string | Record<string, any>

  constructor(
    options: {
      id?: string
      callId?: string
      index?: number
      name?: string
      functionName?: string
      pluginName?: string
      arguments?: string | Record<string, any>
      innerContent?: any
      aiModelId?: string
      metadata?: Record<string, any>
    } = {}
  ) {
    const { id, callId, index, arguments: args, innerContent, aiModelId, metadata } = options

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
    this.index = index
    this.name = name
    this.functionName = functionName || ''
    this.pluginName = pluginName
    this.arguments = args
  }

  /**
   * Return the function call as a string.
   */
  toString(): string {
    const args = typeof this.arguments === 'object' ? JSON.stringify(this.arguments) : this.arguments
    return `${this.name}(${args})`
  }

  /**
   * Add two function calls together, combines the arguments.
   *
   * When both function calls have a dict as arguments, the arguments are merged,
   * which means that the arguments of the second function call
   * will overwrite the arguments of the first function call if the same key is present.
   */
  add(other?: FunctionCallContent): FunctionCallContent {
    if (!other) {
      return this
    }

    if (this.id && other.id && this.id !== other.id) {
      throw new Error('Function calls have different ids.')
    }
    if (this.index !== other.index) {
      throw new Error('Function calls have different indexes.')
    }
    if (this.callId && other.callId && this.callId !== other.callId) {
      throw new Error('Function calls have different call ids.')
    }

    return new FunctionCallContent({
      id: this.id || other.id,
      callId: this.callId || other.callId,
      index: this.index ?? other.index,
      name: this.name || other.name,
      arguments: this.combineArguments(this.arguments, other.arguments),
      metadata: { ...this.metadata, ...other.metadata },
    })
  }

  /**
   * Combine two arguments.
   */
  private combineArguments(
    arg1?: string | Record<string, any>,
    arg2?: string | Record<string, any>
  ): string | Record<string, any> {
    const isArg1Object = typeof arg1 === 'object' && arg1 !== null
    const isArg2Object = typeof arg2 === 'object' && arg2 !== null

    if (isArg1Object && isArg2Object) {
      return { ...arg1, ...arg2 }
    }

    // When one is object and the other isn't, we raise
    if (isArg1Object || isArg2Object) {
      throw new Error('Cannot combine a dict with a string.')
    }

    const arg1Empty = EMPTY_VALUES.includes(arg1 as any)
    const arg2Empty = EMPTY_VALUES.includes(arg2 as any)

    if (arg1Empty && arg2Empty) {
      return '{}'
    }
    if (arg1Empty) {
      return arg2 || '{}'
    }
    if (arg2Empty) {
      return arg1 || '{}'
    }

    return (arg1 || '') + (arg2 || '')
  }

  /**
   * Parse the arguments into a dictionary.
   */
  parseArguments(): Record<string, any> | null {
    if (!this.arguments) {
      return null
    }

    if (typeof this.arguments === 'object') {
      return this.arguments
    }

    try {
      return JSON.parse(this.arguments)
    } catch (error) {
      logger.error('Failed to parse FunctionCallContent arguments as JSON:', error)
      // Try preprocessing: replace single quotes with double quotes
      try {
        const preprocessed = this.arguments.replace(/(?<!\\)'/g, '"').replace(/\\'/g, "'")
        return JSON.parse(preprocessed)
      } catch (error2) {
        throw new Error('Function Call arguments are not valid JSON even after preprocessing.', { cause: error2 })
      }
    }
  }

  /**
   * Return the arguments as a KernelArguments-compatible object.
   */
  toKernelArguments(): Record<string, any> {
    const args = this.parseArguments()
    return args || {}
  }

  /**
   * Split the name into a plugin and function name.
   * @deprecated Use functionName and pluginName properties instead.
   */
  splitName(): [string, string] {
    if (!this.functionName) {
      throw new Error('Function name is not set.')
    }
    return [this.pluginName || '', this.functionName]
  }

  /**
   * Split the name into a plugin and function name as a dictionary.
   * @deprecated Use functionName and pluginName properties instead.
   */
  splitNameDict(): { pluginName?: string; functionName: string } {
    return { pluginName: this.pluginName, functionName: this.functionName }
  }

  /**
   * Get the fully qualified name of the function with a custom separator.
   */
  customFullyQualifiedName(separator: string): string {
    return this.pluginName ? `${this.pluginName}${separator}${this.functionName}` : this.functionName
  }

  /**
   * Convert the function call to an element.
   */
  toElement(): { tag: string; attributes: Record<string, string>; text?: string } {
    const element: { tag: string; attributes: Record<string, string>; text?: string } = {
      tag: this.tag,
      attributes: {},
    }

    if (this.id) {
      element.attributes.id = this.id
    }
    if (this.name) {
      element.attributes.name = this.name
    }
    if (this.arguments) {
      element.text = typeof this.arguments === 'object' ? JSON.stringify(this.arguments) : this.arguments
    }

    return element
  }

  /**
   * Create an instance from an element.
   */
  static fromElement(element: { tag: string; attributes: Record<string, string>; text?: string }): FunctionCallContent {
    if (element.tag !== FUNCTION_CALL_CONTENT_TAG) {
      throw new Error(`Element tag is not ${FUNCTION_CALL_CONTENT_TAG}`)
    }

    return new FunctionCallContent({
      name: element.attributes.name,
      id: element.attributes.id,
      arguments: element.text || '',
    })
  }

  /**
   * Convert the instance to a dictionary.
   */
  toDict(): Record<string, any> {
    const args = typeof this.arguments === 'object' ? JSON.stringify(this.arguments) : this.arguments
    return {
      id: this.id,
      type: 'function',
      function: {
        name: this.name,
        arguments: args,
      },
    }
  }
}
