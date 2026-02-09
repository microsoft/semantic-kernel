import { KernelArguments } from '../functions/kernel-arguments'
import { Kernel } from '../kernel'
import { PromptTemplateConfig } from './prompt-template-config'

/**
 * HTML escape function for string encoding.
 * @param str - The string to escape.
 * @returns The escaped string.
 */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * Base class for prompt templates.
 */
export abstract class PromptTemplateBase {
  /**
   * The prompt template configuration.
   */
  public promptTemplateConfig: PromptTemplateConfig

  /**
   * Allow content without encoding throughout.
   */
  public allowDangerouslySetContent: boolean

  /**
   * Creates a new PromptTemplateBase instance.
   * @param promptTemplateConfig - The prompt template configuration.
   * @param allowDangerouslySetContent - Whether to allow dangerous content without encoding.
   */
  constructor(promptTemplateConfig: PromptTemplateConfig, allowDangerouslySetContent: boolean = false) {
    this.promptTemplateConfig = promptTemplateConfig
    this.allowDangerouslySetContent = allowDangerouslySetContent
  }

  /**
   * Render the prompt template.
   * @param kernel - The kernel instance.
   * @param args - The kernel arguments.
   * @returns The rendered prompt.
   */
  public abstract render(kernel: Kernel, args?: KernelArguments): Promise<string>

  /**
   * Get the trusted arguments.
   *
   * If the prompt template allows unsafe content, then we do not encode the arguments.
   * Otherwise, each argument is checked against the input variables to see if it allowed to be unencoded.
   * For string arguments, applies HTML encoding. For complex types, throws an exception unless
   * allow_dangerously_set_content is set to true.
   *
   * @param args - The kernel arguments.
   * @returns The trusted arguments with encoded values.
   */
  protected _getTrustedArguments(args: KernelArguments): KernelArguments {
    if (this.allowDangerouslySetContent) {
      return args
    }

    const newArgs = new KernelArguments()

    // Copy execution settings
    if (args.executionSettings) {
      newArgs.executionSettings = args.executionSettings
    }

    // Encode each argument
    for (const [name, value] of args.entries()) {
      newArgs.set(name, this._getEncodedValueOrDefault(name, value))
    }

    return newArgs
  }

  /**
   * Get the allow_dangerously_set_content flag.
   *
   * If the prompt template allows unsafe content, then we do not encode the function output,
   * unless explicitly allowed by the prompt template config.
   *
   * @returns Whether to allow dangerously set function output.
   */
  protected _getAllowDangerouslySetFunctionOutput(): boolean {
    let allowDangerouslySetContent = this.allowDangerouslySetContent
    if (this.promptTemplateConfig.allowDangerouslySetContent) {
      allowDangerouslySetContent = true
    }
    return allowDangerouslySetContent
  }

  /**
   * Encode argument value if necessary, or throw an exception if encoding is not supported.
   *
   * @param name - The name of the property/argument.
   * @param value - The value of the property/argument.
   * @returns The encoded value or the original value if encoding is not needed.
   * @throws NotImplementedError if the value is a complex type and allow_dangerously_set_content is False.
   */
  protected _getEncodedValueOrDefault(name: string, value: any): any {
    if (this.allowDangerouslySetContent || this.promptTemplateConfig.allowDangerouslySetContent) {
      return value
    }

    // Check if this variable allows dangerous content
    for (const variable of this.promptTemplateConfig.inputVariables) {
      if (variable.name === name && variable.allowDangerouslySetContent) {
        return value
      }
    }

    if (typeof value === 'string') {
      return escapeHtml(value)
    }

    if (this._isSafeType(value)) {
      return value
    }

    // For complex types, throw an exception if dangerous content is not allowed
    throw new NotImplementedError(
      `Argument '${name}' has a value that doesn't support automatic encoding. ` +
        `Set allow_dangerously_set_content to 'True' for this argument and implement custom encoding, ` +
        `or provide the value as a string.`
    )
  }

  /**
   * Determine if a type is considered safe and doesn't require encoding.
   *
   * @param value - The value to check.
   * @returns True if the type is safe, False otherwise.
   */
  protected _isSafeType(value: any): boolean {
    // Check for primitive types
    if (typeof value === 'number' || typeof value === 'boolean' || value instanceof Buffer) {
      return true
    }

    // Check for Date
    if (value instanceof Date) {
      return true
    }

    // Check for null/undefined
    if (value === null || value === undefined) {
      return true
    }

    return false
  }
}

/**
 * Custom NotImplementedError for encoding not supported.
 */
class NotImplementedError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'NotImplementedError'
  }
}
