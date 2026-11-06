import { KernelContent } from '../contents/kernel-content'
import { KernelFunctionMetadata } from './kernel-function-metadata'

/**
 * Error thrown when function result operations fail.
 */
export class FunctionResultError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionResultError'
  }
}

/**
 * The result of a function execution.
 */
export class FunctionResult {
  /** The metadata of the function that was invoked */
  function: KernelFunctionMetadata

  /** The value of the result */
  value: any

  /** The rendered prompt of the result */
  renderedPrompt?: string

  /** The metadata of the result */
  metadata: Record<string, any>

  constructor(options: {
    function: KernelFunctionMetadata
    value: any
    renderedPrompt?: string
    metadata?: Record<string, any>
  }) {
    this.function = options.function
    this.value = options.value
    this.renderedPrompt = options.renderedPrompt
    this.metadata = options.metadata || {}
  }

  /**
   * Get the string representation of the result.
   * Will call toString() on the value, or if the value is a list,
   * will call toString() on the first element of the list.
   *
   * @returns The string representation of the result
   */
  toString(): string {
    if (this.value) {
      try {
        if (Array.isArray(this.value)) {
          if (this.value.length > 0 && this.value[0] instanceof KernelContent) {
            return String(this.value[0])
          }
          return this.value.map((v) => String(v)).join(',')
        }
        if (typeof this.value === 'object' && this.value !== null && !(this.value instanceof KernelContent)) {
          // TODO: remove this once function result doesn't include input args
          // This is so an integration test can pass.
          const values = Object.values(this.value)
          return String(values[values.length - 1])
        }
        return String(this.value)
      } catch (error) {
        throw new FunctionResultError(`Failed to convert value to string: ${error}`)
      }
    }
    return ''
  }

  /**
   * Get the inner content of the function result.
   *
   * @param index - The index of the inner content if the inner content is a list, default 0
   * @returns The inner content or null
   */
  getInnerContent(index: number = 0): any | null {
    if (Array.isArray(this.value) && this.value[index] instanceof KernelContent) {
      return (this.value[index] as KernelContent).innerContent
    }
    if (this.value instanceof KernelContent) {
      return this.value.innerContent
    }
    return null
  }
}
