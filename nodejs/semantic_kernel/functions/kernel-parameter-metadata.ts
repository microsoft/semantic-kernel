import { KernelJsonSchemaBuilder } from '../schema/kernel-json-schema-builder'
import { FUNCTION_PARAM_NAME_REGEX } from '../utils/validation'

/**
 * Options for creating kernel parameter metadata.
 */
export interface KernelParameterMetadataOptions {
  name: string
  description?: string
  defaultValue?: any
  type?: string
  isRequired?: boolean
  typeObject?: any
  schemaData?: Record<string, any>
  includeInFunctionChoices?: boolean
}

/**
 * The kernel parameter metadata.
 */
export class KernelParameterMetadata {
  name: string
  description?: string
  defaultValue?: any
  type: string
  isRequired: boolean
  typeObject?: any
  schemaData?: Record<string, any>
  includeInFunctionChoices: boolean

  constructor(options: KernelParameterMetadataOptions) {
    const {
      name,
      description,
      defaultValue,
      type = 'str',
      isRequired = false,
      typeObject,
      schemaData,
      includeInFunctionChoices = true,
    } = options

    // Validate parameter name
    if (!FUNCTION_PARAM_NAME_REGEX.test(name)) {
      throw new Error(
        `Invalid parameter name '${name}'. Parameter names must match the pattern: ${FUNCTION_PARAM_NAME_REGEX}`
      )
    }

    this.name = name
    this.description = description
    this.defaultValue = defaultValue
    this.type = type
    this.isRequired = isRequired
    this.typeObject = typeObject
    this.includeInFunctionChoices = includeInFunctionChoices

    // Form schema if not provided
    if (schemaData === undefined) {
      this.schemaData = KernelParameterMetadata.inferSchema(typeObject, type, defaultValue, description)
    } else {
      this.schemaData = schemaData
    }
  }

  /**
   * Infer the schema for the parameter metadata.
   *
   * @param typeObject - The type object
   * @param parameterType - The parameter type string
   * @param defaultValue - The default value
   * @param description - The description
   * @param structuredOutput - Whether to use structured output
   * @returns The inferred schema or undefined
   */
  static inferSchema(
    typeObject?: any,
    parameterType?: string,
    defaultValue?: any,
    description?: string,
    structuredOutput: boolean = false
  ): Record<string, any> | undefined {
    let schema: Record<string, any> | undefined

    if (typeObject !== undefined && typeObject !== null) {
      schema = KernelJsonSchemaBuilder.build(typeObject, {
        description,
        structuredOutput,
      })
    } else if (parameterType !== undefined && parameterType !== null) {
      let finalDescription = description
      const stringDefault = defaultValue !== undefined && defaultValue !== null ? String(defaultValue) : null

      if (stringDefault && stringDefault.trim()) {
        const needsSpace = !!(finalDescription && finalDescription.trim())
        finalDescription = finalDescription
          ? `${finalDescription}${needsSpace ? ' ' : ''}(default value: ${stringDefault})`
          : `(default value: ${stringDefault})`
      }

      schema = KernelJsonSchemaBuilder.buildFromTypeName(parameterType, finalDescription)
    }

    return schema
  }

  /**
   * Convert to a plain object representation.
   */
  toObject(): Record<string, any> {
    return {
      name: this.name,
      description: this.description,
      defaultValue: this.defaultValue,
      type: this.type,
      isRequired: this.isRequired,
      schemaData: this.schemaData,
      includeInFunctionChoices: this.includeInFunctionChoices,
    }
  }

  /**
   * Create from a plain object.
   */
  static fromObject(obj: Record<string, any>): KernelParameterMetadata {
    return new KernelParameterMetadata({
      name: obj.name,
      description: obj.description,
      defaultValue: obj.defaultValue,
      type: obj.type,
      isRequired: obj.isRequired,
      typeObject: obj.typeObject,
      schemaData: obj.schemaData,
      includeInFunctionChoices: obj.includeInFunctionChoices,
    })
  }
}
