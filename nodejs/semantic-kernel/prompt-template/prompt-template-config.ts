import { PromptExecutionSettings } from '../connectors/ai/prompt-execution-settings'
import { DEFAULT_SERVICE_NAME } from '../const'
import { KernelParameterMetadata } from '../functions/kernel-parameter-metadata'
import { KERNEL_TEMPLATE_FORMAT_NAME, TemplateFormatTypes } from './const'
import { InputVariable } from './input-variable'

/**
 * Configuration for a prompt template.
 */
export interface PromptTemplateConfigOptions {
  /**
   * The name of the prompt template.
   */
  name?: string

  /**
   * The description of the prompt template.
   */
  description?: string

  /**
   * The template for the prompt.
   */
  template?: string

  /**
   * The format of the template, should be 'semantic-kernel', 'jinja2' or 'handlebars'.
   */
  templateFormat?: TemplateFormatTypes

  /**
   * The input variables for the prompt.
   */
  inputVariables?: InputVariable[]

  /**
   * Allow content without encoding throughout. This overrides the same settings in the prompt template
   * config and input variables. This reverts the behavior to unencoded input.
   */
  allowDangerouslySetContent?: boolean

  /**
   * The execution settings for the prompt.
   */
  executionSettings?: Map<string, PromptExecutionSettings> | PromptExecutionSettings | PromptExecutionSettings[]
}

/**
 * Configuration for a prompt template.
 */
export class PromptTemplateConfig {
  /**
   * The name of the prompt template.
   */
  public name: string

  /**
   * The description of the prompt template.
   */
  public description: string

  /**
   * The template for the prompt.
   */
  public template: string | null

  /**
   * The format of the template, should be 'semantic-kernel', 'jinja2' or 'handlebars'.
   */
  public templateFormat: TemplateFormatTypes

  /**
   * The input variables for the prompt.
   */
  public inputVariables: InputVariable[]

  /**
   * Allow content without encoding throughout.
   */
  public allowDangerouslySetContent: boolean

  /**
   * The execution settings for the prompt.
   */
  public executionSettings: Map<string, PromptExecutionSettings>

  /**
   * Creates a new PromptTemplateConfig instance.
   * @param options - The configuration options.
   */
  constructor(options: PromptTemplateConfigOptions = {}) {
    this.name = options.name ?? ''
    this.description = options.description ?? ''
    this.template = options.template ?? null
    this.templateFormat = options.templateFormat ?? KERNEL_TEMPLATE_FORMAT_NAME
    this.inputVariables = options.inputVariables ?? []
    this.allowDangerouslySetContent = options.allowDangerouslySetContent ?? false
    this.executionSettings = this.rewriteExecutionSettings(options.executionSettings)

    // Validate input variables
    this.checkInputVariables()
  }

  /**
   * Verify that input variable default values are string only.
   */
  private checkInputVariables(): void {
    for (const variable of this.inputVariables) {
      if (variable.default && typeof variable.default !== 'string') {
        throw new TypeError(`Default value for input variable ${variable.name} must be a string.`)
      }
    }
  }

  /**
   * Rewrite execution settings to a Map.
   */
  private rewriteExecutionSettings(
    settings?: Map<string, PromptExecutionSettings> | PromptExecutionSettings | PromptExecutionSettings[]
  ): Map<string, PromptExecutionSettings> {
    if (!settings) {
      return new Map()
    }
    if (settings instanceof Map) {
      return settings
    }
    if (Array.isArray(settings)) {
      const map = new Map<string, PromptExecutionSettings>()
      for (const s of settings) {
        map.set(s.serviceId || DEFAULT_SERVICE_NAME, s)
      }
      return map
    }
    // Single PromptExecutionSettings
    return new Map([[settings.serviceId || DEFAULT_SERVICE_NAME, settings]])
  }

  /**
   * Add execution settings to the prompt template.
   * @param settings - The execution settings to add.
   * @param overwrite - Whether to overwrite existing settings with the same service ID.
   */
  public addExecutionSettings(settings: PromptExecutionSettings, overwrite: boolean = true): void {
    const serviceId = settings.serviceId || DEFAULT_SERVICE_NAME
    if (this.executionSettings.has(serviceId) && !overwrite) {
      console.warn('Execution settings already exist and overwrite is set to False')
      return
    }
    this.executionSettings.set(serviceId, settings)
  }

  /**
   * Get the kernel parameter metadata for the input variables.
   * @returns The kernel parameter metadata.
   */
  public getKernelParameterMetadata(): KernelParameterMetadata[] {
    return this.inputVariables.map(
      (variable) =>
        new KernelParameterMetadata({
          name: variable.name,
          description: variable.description,
          defaultValue: variable.default,
          type: variable.jsonSchema,
          isRequired: variable.isRequired,
        })
    )
  }

  /**
   * Create a PromptTemplateConfig instance from a JSON string.
   * @param jsonStr - The JSON string to deserialize.
   * @returns A new PromptTemplateConfig instance.
   */
  public static fromJson(jsonStr: string): PromptTemplateConfig {
    if (!jsonStr) {
      throw new ValueError('json_str is empty')
    }
    try {
      const data = JSON.parse(jsonStr)
      return new PromptTemplateConfig({
        name: data.name,
        description: data.description,
        template: data.template,
        templateFormat: data.template_format || data.templateFormat,
        inputVariables: data.input_variables?.map((v: any) => new InputVariable(v)) || data.inputVariables,
        executionSettings: data.execution_settings || data.executionSettings,
        allowDangerouslySetContent: data.allow_dangerously_set_content ?? data.allowDangerouslySetContent,
      })
    } catch (exc) {
      throw new ValueError(
        `Unable to deserialize PromptTemplateConfig from the specified JSON string: ${jsonStr} with exception: ${exc}`
      )
    }
  }

  /**
   * Restore a PromptTemplateConfig instance from the specified parameters.
   * @param options - The configuration options.
   * @returns A new PromptTemplateConfig instance.
   */
  public static restore(options: {
    name: string
    description: string
    template: string
    templateFormat?: TemplateFormatTypes
    inputVariables?: InputVariable[]
    executionSettings?: Map<string, PromptExecutionSettings>
    allowDangerouslySetContent?: boolean
  }): PromptTemplateConfig {
    return new PromptTemplateConfig({
      name: options.name,
      description: options.description,
      template: options.template,
      templateFormat: options.templateFormat ?? KERNEL_TEMPLATE_FORMAT_NAME,
      inputVariables: options.inputVariables ?? [],
      executionSettings: options.executionSettings ?? new Map(),
      allowDangerouslySetContent: options.allowDangerouslySetContent ?? false,
    })
  }
}

/**
 * Custom ValueError for JSON parsing errors.
 */
class ValueError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ValueError'
  }
}
