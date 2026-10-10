const PARSED_ANNOTATION_UNION_DELIMITER = ','

const TYPE_MAPPING: Record<string, string> = {
  int: 'integer',
  str: 'string',
  bool: 'boolean',
  float: 'number',
  list: 'array',
  dict: 'object',
  set: 'array',
  tuple: 'array',
  integer: 'integer',
  string: 'string',
  boolean: 'boolean',
  number: 'number',
  array: 'array',
  object: 'object',
}

/**
 * Options for building JSON schema.
 */
export interface BuildSchemaOptions {
  description?: string
  structuredOutput?: boolean
}

/**
 * Kernel JSON schema builder.
 */
export class KernelJsonSchemaBuilder {
  /**
   * Builds the JSON schema for a given parameter type and description.
   *
   * @param parameterType - The parameter type (constructor, class, string name, or enum)
   * @param options - Options including description and structuredOutput flag
   * @returns The JSON schema for the parameter type
   */
  static build(parameterType: any, options: BuildSchemaOptions = {}): Record<string, any> {
    const { description, structuredOutput = false } = options

    // Handle string type names
    if (typeof parameterType === 'string') {
      return this.buildFromTypeName(parameterType, description)
    }

    // Handle enum types
    if (this.isEnum(parameterType)) {
      return this.buildEnumSchema(parameterType, description)
    }

    // Handle class/interface with properties
    if (typeof parameterType === 'function' || typeof parameterType === 'object') {
      // Check if it's a class constructor or has a schema method
      if (this.hasSchema(parameterType)) {
        return this.buildModelSchema(parameterType, description, structuredOutput)
      }
    }

    // Handle arrays, objects, and union types
    if (this.isComplexType(parameterType)) {
      return this.handleComplexType(parameterType, description, structuredOutput)
    }

    // Default: get basic schema
    const schema = this.getJsonSchema(parameterType)
    if (description) {
      schema.description = description
    }
    return schema
  }

  /**
   * Builds the JSON schema for a given model and description.
   *
   * @param model - The model type or class
   * @param description - The description of the model
   * @param structuredOutput - Whether the outputs are structured
   * @returns The JSON schema for the model
   */
  static buildModelSchema(model: any, description?: string, structuredOutput: boolean = false): Record<string, any> {
    const properties: Record<string, any> = {}
    const required: string[] = []

    // Get properties from the model
    // This could be from TypeScript class properties, Zod schema, or other schema definitions
    const modelProperties = this.getModelProperties(model)

    for (const [fieldName, fieldInfo] of Object.entries(modelProperties)) {
      const fieldType = (fieldInfo as any).type
      const fieldDescription = (fieldInfo as any).description
      const isOptional = (fieldInfo as any).optional

      if (!isOptional) {
        required.push(fieldName)
      }

      properties[fieldName] = this.build(fieldType, {
        description: fieldDescription,
        structuredOutput,
      })
    }

    const schema: Record<string, any> = {
      type: 'object',
      properties,
    }

    if (required.length > 0) {
      schema.required = required
    }

    if (structuredOutput) {
      schema.additionalProperties = false
    }

    if (description) {
      schema.description = description
    }

    return schema
  }

  /**
   * Builds the JSON schema for a given parameter type name and description.
   *
   * @param parameterType - The parameter type name
   * @param description - The description of the parameter
   * @returns The JSON schema for the parameter type
   */
  static buildFromTypeName(parameterType: string, description?: string): Record<string, any> {
    const schema: Record<string, any> = {}

    if (parameterType.includes(PARSED_ANNOTATION_UNION_DELIMITER)) {
      // This means it is a Union or | so need to build with "anyOf"
      const types = parameterType.split(PARSED_ANNOTATION_UNION_DELIMITER)
      const schemas = types.map((t) => this.buildFromTypeName(t.trim(), description))
      schema.anyOf = schemas
    } else {
      const typeName = TYPE_MAPPING[parameterType] || 'object'
      schema.type = typeName
      if (description) {
        schema.description = description
      }
    }

    return schema
  }

  /**
   * Gets JSON schema for a given parameter type.
   *
   * @param parameterType - The parameter type
   * @returns The JSON schema for the parameter type
   */
  static getJsonSchema(parameterType: any): Record<string, any> {
    const typeName = this.getTypeName(parameterType)
    const mappedType = TYPE_MAPPING[typeName] || 'object'
    return { type: mappedType }
  }

  /**
   * Handles building the JSON schema for complex types.
   *
   * @param parameterType - The parameter type
   * @param description - The description of the parameter
   * @param structuredOutput - Whether the outputs are structured
   * @returns The JSON schema for the parameter type
   */
  static handleComplexType(
    parameterType: any,
    description?: string,
    structuredOutput: boolean = false
  ): Record<string, any> {
    let schema: Record<string, any>

    // Handle Array types
    if (this.isArrayType(parameterType)) {
      const itemType = this.getArrayItemType(parameterType)
      schema = {
        type: 'array',
        items: this.build(itemType, { structuredOutput }),
      }
      if (description) {
        schema.description = description
      }
      return schema
    }

    // Handle Object/Record types with specific value types
    if (this.isRecordType(parameterType)) {
      const valueType = this.getRecordValueType(parameterType)
      const additionalProperties = this.build(valueType, { structuredOutput })

      if (additionalProperties.type === 'object' && !additionalProperties.properties) {
        additionalProperties.properties = {}
      }

      schema = {
        type: 'object',
        additionalProperties,
      }

      if (description) {
        schema.description = description
      }

      if (structuredOutput) {
        schema.additionalProperties = false
      }

      return schema
    }

    // Handle Union types
    if (this.isUnionType(parameterType)) {
      const unionTypes = this.getUnionTypes(parameterType)

      // Handle Optional (Union with null/undefined)
      if (unionTypes.length === 2 && this.hasNullType(unionTypes)) {
        const nonNullType = unionTypes.find((t) => !this.isNullType(t))
        schema = this.build(nonNullType, { structuredOutput })
        schema.type = [schema.type, 'null']
        if (description) {
          schema.description = description
        }
        if (structuredOutput) {
          schema.additionalProperties = false
        }
        return schema
      }

      // General union
      const schemas = unionTypes.map((arg) => this.build(arg, { description, structuredOutput }))
      return { anyOf: schemas }
    }

    // Default fallback
    schema = this.getJsonSchema(parameterType)
    if (description) {
      schema.description = description
    }
    if (structuredOutput) {
      schema.additionalProperties = false
    }
    return schema
  }

  /**
   * Builds the JSON schema for an enum type.
   *
   * @param enumType - The enum type
   * @param description - The description of the enum
   * @returns The JSON schema for the enum type
   */
  static buildEnumSchema(enumType: any, description?: string): Record<string, any> {
    if (!this.isEnum(enumType)) {
      throw new Error(`${enumType} is not a valid Enum type`)
    }

    try {
      const enumValues = Object.values(enumType).filter((value) => typeof value !== 'function')

      const firstValueType = typeof enumValues[0]
      const mappedType = TYPE_MAPPING[firstValueType] || 'string'

      const schema: Record<string, any> = {
        type: mappedType,
        enum: enumValues,
      }

      if (description) {
        schema.description = description
      }

      return schema
    } catch (error) {
      throw new Error(
        `Failed to get enum values for ${enumType}: ${error instanceof Error ? error.message : String(error)}`,
        { cause: error }
      )
    }
  }

  // Helper methods

  private static isEnum(value: any): boolean {
    return (
      typeof value === 'object' &&
      value !== null &&
      Object.values(value).some((v) => typeof v === 'string' || typeof v === 'number')
    )
  }

  private static hasSchema(value: any): boolean {
    return typeof value === 'function' || (typeof value === 'object' && value !== null && 'schema' in value)
  }

  private static isComplexType(value: any): boolean {
    // Check if it's an array, record, or union type indicator
    return this.isArrayType(value) || this.isRecordType(value) || this.isUnionType(value)
  }

  private static isArrayType(value: any): boolean {
    return Array.isArray(value) || (typeof value === 'object' && value?._type === 'array')
  }

  private static isRecordType(value: any): boolean {
    return typeof value === 'object' && value?._type === 'record'
  }

  private static isUnionType(value: any): boolean {
    return typeof value === 'object' && value?._type === 'union'
  }

  private static getArrayItemType(value: any): any {
    if (Array.isArray(value) && value.length > 0) {
      return value[0]
    }
    return value?.itemType || 'object'
  }

  private static getRecordValueType(value: any): any {
    return value?.valueType || 'object'
  }

  private static getUnionTypes(value: any): any[] {
    return value?.types || []
  }

  private static hasNullType(types: any[]): boolean {
    return types.some((t) => this.isNullType(t))
  }

  private static isNullType(value: any): boolean {
    return value === null || value === undefined || value === 'null' || value === 'undefined'
  }

  private static getTypeName(value: any): string {
    if (typeof value === 'string') {
      return value
    }
    if (typeof value === 'function') {
      return value.name.toLowerCase()
    }
    if (typeof value === 'object' && value !== null) {
      return value.constructor?.name?.toLowerCase() || 'object'
    }
    return typeof value
  }

  private static getModelProperties(model: any): Record<string, any> {
    const properties: Record<string, any> = {}

    // Handle Zod schemas
    if (model && typeof model === 'object' && 'shape' in model) {
      const shape = model.shape
      for (const [key, value] of Object.entries(shape)) {
        properties[key] = {
          type: value,
          optional: (value as any)?.isOptional?.() || false,
          description: (value as any)?._def?.description,
        }
      }
      return properties
    }

    // Handle class constructors with metadata
    if (typeof model === 'function') {
      // This would need to be implemented based on how TypeScript classes
      // expose their metadata (e.g., through decorators or reflection)
      // For now, return empty properties
      return properties
    }

    return properties
  }
}
