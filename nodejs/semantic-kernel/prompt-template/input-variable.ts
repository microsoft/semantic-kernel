/**
 * Configuration for an input variable in a prompt template.
 */
export interface InputVariableConfig {
  /**
   * The name of the input variable.
   */
  name: string

  /**
   * The description of the input variable.
   */
  description?: string

  /**
   * The default value of the input variable.
   */
  default?: any

  /**
   * Whether the input variable is required.
   */
  isRequired?: boolean

  /**
   * The JSON schema for the input variable.
   */
  jsonSchema?: string

  /**
   * Allow content without encoding. This controls if this variable is encoded before use.
   * Default is false.
   */
  allowDangerouslySetContent?: boolean
}

/**
 * Input variable for a prompt template.
 */
export class InputVariable {
  /**
   * The name of the input variable.
   */
  public name: string

  /**
   * The description of the input variable.
   */
  public description: string

  /**
   * The default value of the input variable.
   */
  public default: any

  /**
   * Whether the input variable is required.
   */
  public isRequired: boolean

  /**
   * The JSON schema for the input variable.
   */
  public jsonSchema: string

  /**
   * Allow content without encoding. This controls if this variable is encoded before use.
   */
  public allowDangerouslySetContent: boolean

  /**
   * Creates a new InputVariable instance.
   * @param config - The configuration for the input variable.
   */
  constructor(config: InputVariableConfig) {
    this.name = config.name
    this.description = config.description ?? ''
    this.default = config.default ?? ''
    this.isRequired = config.isRequired ?? true
    this.jsonSchema = config.jsonSchema ?? ''
    this.allowDangerouslySetContent = config.allowDangerouslySetContent ?? false
  }
}
