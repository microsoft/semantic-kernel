/**
 * Base class for all function exceptions.
 */
export class FunctionException extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionException'
  }
}

/**
 * Base class for all function syntax exceptions.
 */
export class FunctionSyntaxError extends FunctionException {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionSyntaxError'
  }
}

/**
 * An error occurred while initializing the function.
 */
export class FunctionInitializationError extends FunctionException {
  constructor(message: string) {
    super('KernelFunction failed to initialize: ' + message)
    this.name = 'FunctionInitializationError'
  }
}

/**
 * An error occurred while initializing the plugin.
 */
export class PluginInitializationError extends FunctionException {
  constructor(message: string) {
    super(message)
    this.name = 'PluginInitializationError'
  }
}

/**
 * An error occurred while validating the plugin name.
 */
export class PluginInvalidNameError extends FunctionSyntaxError {
  constructor(message: string) {
    super(message)
    this.name = 'PluginInvalidNameError'
  }
}

/**
 * An error occurred while validating the function name.
 */
export class FunctionInvalidNameError extends FunctionSyntaxError {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionInvalidNameError'
  }
}

/**
 * An error occurred while validating the function parameter name.
 */
export class FunctionInvalidParamNameError extends FunctionSyntaxError {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionInvalidParamNameError'
  }
}

/**
 * An error occurred while validating the function name uniqueness.
 */
export class FunctionNameNotUniqueError extends FunctionSyntaxError {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionNameNotUniqueError'
  }
}

/**
 * Base class for all function execution exceptions.
 */
export class FunctionExecutionException extends FunctionException {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionExecutionException'
  }
}

/**
 * An error occurred while validating the function result.
 */
export class FunctionResultError extends FunctionException {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionResultError'
  }
}

/**
 * An error occurred while validating the function parameter configuration.
 */
export class FunctionInvalidParameterConfiguration extends FunctionException {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionInvalidParameterConfiguration'
  }
}

/**
 * An error occurred while rendering a prompt.
 */
export class PromptRenderingException extends FunctionException {
  constructor(message: string) {
    super(message)
    this.name = 'PromptRenderingException'
  }
}
