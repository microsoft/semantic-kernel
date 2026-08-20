import { FilterTypes } from '../filters/filter-types'
import { FunctionInvocationContext } from '../filters/functions/function-invocation-context'
import { KernelFunction as IKernelFunction, Kernel } from '../kernel'
import { PromptTemplateConfig } from '../prompt-template/prompt-template-config'
import { createDefaultLogger, Logger } from '../utils/logger'
import { FunctionResult } from './function-result'
import { KernelArguments } from './kernel-arguments'
import { KernelFunctionMetadata } from './kernel-function-metadata'
import { KernelParameterMetadata } from './kernel-parameter-metadata'

const logger: Logger = createDefaultLogger('KernelFunction')

/**
 * Histogram for tracking function invocation duration.
 */
interface DurationHistogram {
  record(duration: number, attributes: Record<string, string>): void
}

/**
 * Abstract base class for all kernel functions.
 */
export abstract class KernelFunction implements IKernelFunction {
  /**
   * The metadata for this function.
   */
  metadata: KernelFunctionMetadata

  /**
   * Histogram for tracking invocation duration.
   */
  protected invocationDurationHistogram: DurationHistogram | null = null

  /**
   * Histogram for tracking streaming invocation duration.
   */
  protected streamingDurationHistogram: DurationHistogram | null = null

  /**
   * Constructor.
   * @param metadata - The function metadata.
   */
  constructor(metadata: KernelFunctionMetadata) {
    this.metadata = metadata
  }

  /**
   * Create a kernel function from a prompt template.
   * @param _functionName - The name of the function.
   * @param _pluginName - The name of the plugin.
   * @param _description - The description of the function.
   * @param _templateConfig - The prompt template configuration.
   * @param _templateFormatName - The template format name.
   * @returns A new KernelFunctionFromPrompt instance.
   */
  static fromPrompt(
    _functionName: string,
    _pluginName?: string,
    _description?: string,
    _templateConfig?: PromptTemplateConfig,
    _templateFormatName?: string
  ): KernelFunction {
    // This will be implemented by KernelFunctionFromPrompt
    throw new Error('Not implemented - use KernelFunctionFromPrompt.fromPrompt')
  }

  /**
   * Create a kernel function from a method.
   * @param _method - The method to wrap.
   * @param _pluginName - The name of the plugin.
   * @param _functionName - The name of the function.
   * @param _description - The description of the function.
   * @param _parameters - The function parameters.
   * @param _returnParameter - The return parameter.
   * @returns A new KernelFunctionFromMethod instance.
   */
  static fromMethod(
    _method: (...args: any[]) => any,
    _pluginName?: string,
    _functionName?: string,
    _description?: string,
    _parameters?: KernelParameterMetadata[],
    _returnParameter?: KernelParameterMetadata
  ): KernelFunction {
    // This will be implemented by KernelFunctionFromMethod
    throw new Error('Not implemented - use KernelFunctionFromMethod.fromMethod')
  }

  /**
   * Get the name of the function.
   */
  get name(): string {
    return this.metadata.name
  }

  /**
   * Get the plugin name.
   */
  get pluginName(): string | undefined {
    return this.metadata.pluginName
  }

  /**
   * Get the fully qualified name of the function.
   */
  get fullyQualifiedName(): string {
    return this.metadata.fullyQualifiedName
  }

  /**
   * Get the description of the function.
   */
  get description(): string | undefined {
    return this.metadata.description
  }

  /**
   * Check if this is a prompt function.
   */
  get isPrompt(): boolean {
    return this.metadata.isPrompt ?? false
  }

  /**
   * Get the function parameters.
   */
  get parameters(): KernelParameterMetadata[] {
    return this.metadata.parameters
  }

  /**
   * Get the return parameter.
   */
  get returnParameter(): KernelParameterMetadata | undefined {
    return this.metadata.returnParameter
  }

  /**
   * Invoke the function with the given arguments.
   * @param kernel - The kernel instance.
   * @param arguments_ - The kernel arguments.
   * @param _metadata - Additional metadata.
   * @returns A promise that resolves to a FunctionResult.
   */
  async invoke(kernel: Kernel, arguments_: KernelArguments, _metadata?: Record<string, any>): Promise<FunctionResult> {
    // Create function invocation context
    const functionContext = new FunctionInvocationContext({
      function: this,
      kernel,
      arguments: arguments_,
      isStreaming: false,
    })

    // Start tracing span (simplified - full OpenTelemetry integration would go here)
    const startTime = performance.now()
    const attributes: Record<string, string> = {
      'function.name': this.fullyQualifiedName,
    }

    try {
      // Log function invocation
      logger.debug(`Invoking function: ${this.fullyQualifiedName}`)
      logger.debug(`Function arguments: ${JSON.stringify(arguments_)}`)

      // Construct filter call stack
      const stack = kernel.constructCallStack(FilterTypes.FUNCTION_INVOCATION, this._invokeInternal.bind(this))

      // Execute the function through the filter chain
      await stack(functionContext)

      // Log success
      logger.debug(`Function invoked successfully: ${this.fullyQualifiedName}`)

      // Return the result
      if (!functionContext.result) {
        throw new Error('Function did not produce a result')
      }

      return functionContext.result
    } catch (error) {
      // Handle exception
      this._handleException(error as Error, attributes)
      throw error
    } finally {
      // Record duration
      const duration = performance.now() - startTime
      if (this.invocationDurationHistogram) {
        this.invocationDurationHistogram.record(duration, attributes)
      }
      logger.debug(`Function completed in ${duration}ms`)
    }
  }

  /**
   * Internal invoke method - to be implemented by subclasses.
   * @param context - The function invocation context.
   */
  protected abstract _invokeInternal(context: FunctionInvocationContext): Promise<void>

  /**
   * Invoke the function in streaming mode.
   * @param kernel - The kernel instance.
   * @param arguments_ - The kernel arguments.
   * @returns An async generator that yields streaming content or FunctionResult.
   */
  async *invokeStream(kernel: Kernel, arguments_: KernelArguments): AsyncGenerator<any, void, unknown> {
    // Create function invocation context
    const functionContext = new FunctionInvocationContext({
      function: this,
      kernel,
      arguments: arguments_,
      isStreaming: true,
    })

    // Start timing
    const startTime = performance.now()
    const attributes: Record<string, string> = {
      'function.name': this.fullyQualifiedName,
    }

    try {
      // Log function invocation
      logger.debug(`Invoking streaming function: ${this.fullyQualifiedName}`)
      logger.debug(`Function arguments: ${JSON.stringify(arguments_)}`)

      // Construct filter call stack
      const stack = kernel.constructCallStack(FilterTypes.FUNCTION_INVOCATION, this._invokeInternalStream.bind(this))

      // Execute the function through the filter chain
      await stack(functionContext)

      // Process and yield results
      const functionResults: any[] = []
      if (functionContext.result) {
        const resultValue = functionContext.result.value

        // Check if it's an async generator
        if (resultValue && typeof resultValue[Symbol.asyncIterator] === 'function') {
          for await (const partial of resultValue) {
            functionResults.push(partial)
            yield partial
          }
        }
        // Check if it's a regular generator
        else if (resultValue && typeof resultValue[Symbol.iterator] === 'function') {
          for (const partial of resultValue) {
            functionResults.push(partial)
            yield partial
          }
        }
        // Single result
        else {
          functionResults.push(resultValue)
          yield functionContext.result
        }
      }

      // Log results
      logger.debug(`Streaming results: ${JSON.stringify(functionResults)}`)
    } catch (error) {
      // Handle exception
      this._handleException(error as Error, attributes)
      throw error
    } finally {
      // Record duration
      const duration = performance.now() - startTime
      if (this.streamingDurationHistogram) {
        this.streamingDurationHistogram.record(duration, attributes)
      }
      logger.debug(`Streaming function completed in ${duration}ms`)
    }
  }

  /**
   * Internal streaming invoke method - to be implemented by subclasses.
   * @param context - The function invocation context.
   */
  protected abstract _invokeInternalStream(context: FunctionInvocationContext): Promise<void>

  /**
   * Create a copy of this function, optionally with a new plugin name.
   * @param pluginName - The new plugin name.
   * @returns A copy of this function.
   */
  functionCopy(pluginName?: string): KernelFunction {
    // Create a shallow copy
    const copy = Object.create(Object.getPrototypeOf(this))
    Object.assign(copy, this)

    // Deep copy the metadata
    copy.metadata = { ...this.metadata }
    if (pluginName) {
      copy.metadata.pluginName = pluginName
      copy.metadata.fullyQualifiedName = `${pluginName}-${this.metadata.name}`
    }

    return copy
  }

  /**
   * Handle an exception during function invocation.
   * @param error - The error that occurred.
   * @param attributes - Attributes to update.
   */
  protected _handleException(error: Error, attributes: Record<string, string>): void {
    attributes['error.type'] = error.name

    // Log the error
    logger.error(`Function error: ${error.message}`, error)

    // In a full implementation, this would set span attributes and status
    // For now, we just log it
  }
}
