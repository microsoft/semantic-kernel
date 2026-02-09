import { FunctionExecutionException, FunctionInitializationError } from '../exceptions/function-exceptions'
import type { FunctionInvocationContext } from '../filters/functions/function-invocation-context'
import { FunctionResult } from './function-result'
import { KernelFunction } from './kernel-function'
import { KernelFunctionMetadata } from './kernel-function-metadata'
import { KernelParameterMetadata } from './kernel-parameter-metadata'

/**
 * Semantic Kernel Function from a method.
 */
export class KernelFunctionFromMethod extends KernelFunction {
  method: (...args: any[]) => any
  streamMethod?: ((...args: any[]) => any) | null = null

  constructor(params: {
    method: (...args: any[]) => any
    name?: string
    description?: string
    pluginName?: string | null
    streamMethod?: ((...args: any[]) => any) | null
    parameters?: KernelParameterMetadata[] | null
    returnParameter?: KernelParameterMetadata | null
    additionalMetadata?: Record<string, any> | null
  }) {
    const {
      method,
      name,
      description,
      pluginName = null,
      streamMethod = null,
      parameters = null,
      returnParameter = null,
      additionalMetadata = null,
    } = params

    if (!method) {
      throw new FunctionInitializationError('Method cannot be null')
    }

    // Check if method has kernel function metadata
    const methodAny = method as any
    if (!methodAny.__kernel_function__) {
      // If no kernel function metadata, use provided name and description
      // This allows creating functions from plain methods
      if (!name) {
        throw new FunctionInitializationError('Method is not a Kernel function and no name was provided')
      }
    }

    // Extract function metadata from decorated method or use provided values
    const functionName = name || methodAny.__kernel_function_name__
    const functionDescription = description || methodAny.__kernel_function_description__ || ''

    let functionParameters: KernelParameterMetadata[]
    if (parameters === null) {
      if (methodAny.__kernel_function_parameters__) {
        functionParameters = methodAny.__kernel_function_parameters__.map(
          (param: any) => new KernelParameterMetadata(param)
        )
      } else {
        functionParameters = []
      }
    } else {
      functionParameters = parameters
    }

    let functionReturnParameter: KernelParameterMetadata
    if (returnParameter === null) {
      if (methodAny.__kernel_function_return_description__) {
        functionReturnParameter = new KernelParameterMetadata({
          name: 'return',
          description: methodAny.__kernel_function_return_description__,
          defaultValue: null,
          type: methodAny.__kernel_function_return_type__,
          typeObject: methodAny.__kernel_function_return_type_object__,
          isRequired: methodAny.__kernel_function_return_required__,
        })
      } else {
        functionReturnParameter = new KernelParameterMetadata({
          name: 'return',
          description: '',
          isRequired: false,
        })
      }
    } else {
      functionReturnParameter = returnParameter
    }

    // Check if method is async
    const isAsynchronous =
      method.constructor.name === 'AsyncFunction' || method.constructor.name === 'AsyncGeneratorFunction'

    let metadata: KernelFunctionMetadata
    try {
      metadata = new KernelFunctionMetadata({
        name: functionName,
        description: functionDescription,
        parameters: functionParameters,
        returnParameter: functionReturnParameter,
        isPrompt: false,
        isAsynchronous,
        pluginName: pluginName ?? undefined,
        additionalProperties: additionalMetadata || {},
      })
    } catch (error) {
      console.error('Error creating KernelFunctionMetadata:', error)
      throw new FunctionInitializationError('Failed to create KernelFunctionMetadata')
    }

    super(metadata)

    this.method = method
    this.streamMethod =
      streamMethod !== null
        ? streamMethod
        : method.constructor.name === 'AsyncGeneratorFunction' || method.constructor.name === 'GeneratorFunction'
          ? method
          : null
  }

  /**
   * Invoke the function with the given arguments.
   */
  protected async _invokeInternal(context: FunctionInvocationContext): Promise<void> {
    const functionArguments = this.gatherFunctionParameters(context)
    let result = this.method(...Object.values(functionArguments))

    // Handle async generators
    if (result && typeof result[Symbol.asyncIterator] === 'function') {
      const items: any[] = []
      for await (const item of result) {
        items.push(item)
      }
      result = items
    }
    // Handle promises
    else if (result && typeof result.then === 'function') {
      result = await result
    }
    // Handle sync generators
    else if (result && typeof result[Symbol.iterator] === 'function') {
      result = Array.from(result)
    }

    if (!(result instanceof FunctionResult)) {
      result = new FunctionResult({
        function: this.metadata,
        value: result,
        metadata: { arguments: context.arguments, usedArguments: functionArguments },
      })
    }

    context.result = result
  }

  /**
   * Invoke the function with streaming.
   */
  protected async _invokeInternalStream(context: FunctionInvocationContext): Promise<void> {
    if (!this.streamMethod) {
      throw new Error('Stream method not implemented')
    }

    const functionArguments = this.gatherFunctionParameters(context)
    context.result = new FunctionResult({
      function: this.metadata,
      value: this.streamMethod(...Object.values(functionArguments)),
    })
  }

  /**
   * Parses the value into the specified param type, including handling lists of types.
   */
  private _parseParameter(value: any, paramType: any): any {
    // Handle Any or object type explicitly
    if (paramType === undefined || paramType === null || paramType === Object) {
      return value
    }

    // Handle Pydantic-like models with model_validate
    if (typeof paramType === 'function' && typeof (paramType as any).model_validate === 'function') {
      try {
        return (paramType as any).model_validate(value)
      } catch (error) {
        console.error('Error validating parameter with model_validate:', error)
        throw new FunctionExecutionException(`Parameter is expected to be parsed to ${paramType} but is not.`)
      }
    }

    // Handle Array types
    if (Array.isArray(value) && paramType === Array) {
      return value
    }

    // Try to construct the type
    try {
      if (typeof value === 'object' && value !== null && typeof paramType === 'function') {
        return new paramType(value)
      }
      return paramType(value)
    } catch (error) {
      console.error('Error parsing parameter:', error)
      throw new FunctionExecutionException(`Parameter is expected to be parsed to ${paramType} but is not.`)
    }
  }

  /**
   * Gathers the function parameters from the arguments.
   */
  gatherFunctionParameters(context: FunctionInvocationContext): Record<string, any> {
    const functionArguments: Record<string, any> = {}

    for (const param of this.parameters) {
      if (!param.name) {
        throw new FunctionExecutionException('Parameter name cannot be null')
      }

      // Handle special parameter names
      if (param.name === 'kernel') {
        functionArguments[param.name] = context.kernel
        continue
      }
      if (param.name === 'service') {
        // Get the service from kernel
        functionArguments[param.name] = context.kernel.getService()
        continue
      }
      if (param.name === 'execution_settings') {
        // Execution settings would typically come from context or arguments
        functionArguments[param.name] = null
        continue
      }
      if (param.name === 'arguments') {
        functionArguments[param.name] = context.arguments
        continue
      }

      // Check if argument is provided
      if (context.arguments.has(param.name)) {
        let value: any = context.arguments.get(param.name)

        if (param.type && !param.type.includes(',') && param.typeObject && param.typeObject !== Object) {
          try {
            value = this._parseParameter(value, param.typeObject)
          } catch (error) {
            console.error(`Error parsing parameter ${param.name}:`, error)
            throw new FunctionExecutionException(
              `Parameter ${param.name} is expected to be parsed to ${param.typeObject} but is not.`
            )
          }
        }

        functionArguments[param.name] = value
        continue
      }

      // Check if parameter is required
      if (param.isRequired) {
        throw new FunctionExecutionException(`Parameter ${param.name} is required but not provided in the arguments.`)
      }

      console.debug(`Parameter ${param.name} is not provided, using default value ${param.defaultValue}`)
    }

    return functionArguments
  }
}
