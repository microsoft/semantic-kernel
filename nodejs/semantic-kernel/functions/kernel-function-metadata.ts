import { FUNCTION_NAME_REGEX, PLUGIN_NAME_REGEX } from '../utils/validation'
import { KernelParameterMetadata } from './kernel-parameter-metadata'

const DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR = '-'

/**
 * Options for creating kernel function metadata.
 */
export interface KernelFunctionMetadataOptions {
  name: string
  pluginName?: string
  description?: string
  parameters?: KernelParameterMetadata[]
  isPrompt: boolean
  isAsynchronous?: boolean
  returnParameter?: KernelParameterMetadata
  additionalProperties?: Record<string, any>
}

/**
 * The kernel function metadata.
 */
export class KernelFunctionMetadata {
  name: string
  pluginName?: string
  description?: string
  parameters: KernelParameterMetadata[]
  isPrompt: boolean
  isAsynchronous: boolean
  returnParameter?: KernelParameterMetadata
  additionalProperties?: Record<string, any>

  constructor(options: KernelFunctionMetadataOptions) {
    const {
      name,
      pluginName,
      description,
      parameters = [],
      isPrompt,
      isAsynchronous = true,
      returnParameter,
      additionalProperties,
    } = options

    // Validate function name
    if (!name || !FUNCTION_NAME_REGEX.test(name)) {
      throw new Error(`Invalid function name '${name}'. Function names must match the pattern: ${FUNCTION_NAME_REGEX}`)
    }

    // Validate plugin name if provided
    if (pluginName && !PLUGIN_NAME_REGEX.test(pluginName)) {
      throw new Error(`Invalid plugin name '${pluginName}'. Plugin names must match the pattern: ${PLUGIN_NAME_REGEX}`)
    }

    this.name = name
    this.pluginName = pluginName
    this.description = description
    this.parameters = parameters
    this.isPrompt = isPrompt
    this.isAsynchronous = isAsynchronous
    this.returnParameter = returnParameter
    this.additionalProperties = additionalProperties
  }

  /**
   * Get the fully qualified name of the function.
   *
   * A fully qualified name is the name of the combination of the plugin name and
   * the function name, separated by a hyphen, if the plugin name is present.
   * Otherwise, it is just the function name.
   */
  get fullyQualifiedName(): string {
    return this.customFullyQualifiedName(DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR)
  }

  /**
   * Get the fully qualified name of the function with a custom separator.
   *
   * @param separator - The custom separator
   * @returns The fully qualified name of the function with a custom separator
   */
  customFullyQualifiedName(separator: string): string {
    return this.pluginName ? `${this.pluginName}${separator}${this.name}` : this.name
  }

  /**
   * Compare to another KernelFunctionMetadata instance.
   *
   * @param other - The other KernelFunctionMetadata instance
   * @returns True if the two instances are equal, False otherwise
   */
  equals(other: any): boolean {
    if (!(other instanceof KernelFunctionMetadata)) {
      return false
    }

    return (
      this.name === other.name &&
      this.pluginName === other.pluginName &&
      this.description === other.description &&
      this.isPrompt === other.isPrompt &&
      this.isAsynchronous === other.isAsynchronous &&
      this.parametersEqual(other.parameters) &&
      this.returnParameterEqual(other.returnParameter)
    )
  }

  /**
   * Check if parameters are equal.
   *
   * @private
   */
  private parametersEqual(otherParameters: KernelParameterMetadata[]): boolean {
    if (this.parameters.length !== otherParameters.length) {
      return false
    }

    for (let i = 0; i < this.parameters.length; i++) {
      const thisParam = this.parameters[i]
      const otherParam = otherParameters[i]

      if (
        thisParam.name !== otherParam.name ||
        thisParam.description !== otherParam.description ||
        thisParam.defaultValue !== otherParam.defaultValue ||
        thisParam.type !== otherParam.type ||
        thisParam.isRequired !== otherParam.isRequired
      ) {
        return false
      }
    }

    return true
  }

  /**
   * Check if return parameters are equal.
   *
   * @private
   */
  private returnParameterEqual(otherReturnParameter?: KernelParameterMetadata): boolean {
    if (!this.returnParameter && !otherReturnParameter) {
      return true
    }

    if (!this.returnParameter || !otherReturnParameter) {
      return false
    }

    return (
      this.returnParameter.name === otherReturnParameter.name &&
      this.returnParameter.description === otherReturnParameter.description &&
      this.returnParameter.type === otherReturnParameter.type
    )
  }

  /**
   * Convert to a plain object representation.
   */
  toObject(): Record<string, any> {
    return {
      name: this.name,
      pluginName: this.pluginName,
      description: this.description,
      parameters: this.parameters.map((p) => p.toObject()),
      isPrompt: this.isPrompt,
      isAsynchronous: this.isAsynchronous,
      returnParameter: this.returnParameter?.toObject(),
      additionalProperties: this.additionalProperties,
    }
  }

  /**
   * Create from a plain object.
   */
  static fromObject(obj: Record<string, any>): KernelFunctionMetadata {
    return new KernelFunctionMetadata({
      name: obj.name,
      pluginName: obj.pluginName,
      description: obj.description,
      parameters: obj.parameters?.map((p: any) => KernelParameterMetadata.fromObject(p)),
      isPrompt: obj.isPrompt,
      isAsynchronous: obj.isAsynchronous,
      returnParameter: obj.returnParameter ? KernelParameterMetadata.fromObject(obj.returnParameter) : undefined,
      additionalProperties: obj.additionalProperties,
    })
  }
}
