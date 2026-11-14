import { FunctionChoiceBehavior } from './function-choice-behavior'

/**
 * Base class for prompt execution settings.
 *
 * Can be used by itself or as a base class for other prompt execution settings. The methods are used to create
 * specific prompt execution settings objects based on the keys in the extensionData field, this way you can
 * create a generic PromptExecutionSettings object in your application, which gets mapped into the keys of the
 * prompt execution settings that each service returns by using the service.getPromptExecutionSettings() method.
 */
export class PromptExecutionSettings {
  serviceId?: string
  extensionData: Record<string, any>
  functionChoiceBehavior?: FunctionChoiceBehavior

  constructor(options?: {
    serviceId?: string
    extensionData?: Record<string, any>
    functionChoiceBehavior?: FunctionChoiceBehavior | string | Record<string, any>
    [key: string]: any
  }) {
    const { serviceId, extensionData = {}, functionChoiceBehavior, ...kwargs } = options || {}

    // Validate serviceId
    if (serviceId !== undefined && serviceId !== null) {
      const trimmed = serviceId.trim()
      if (trimmed.length === 0) {
        throw new Error('serviceId must be at least 1 character long')
      }
      this.serviceId = trimmed
    }

    // Parse function choice behavior
    if (functionChoiceBehavior) {
      if (typeof functionChoiceBehavior === 'string') {
        this.functionChoiceBehavior = FunctionChoiceBehavior.fromString(functionChoiceBehavior)
      } else if (functionChoiceBehavior instanceof FunctionChoiceBehavior) {
        this.functionChoiceBehavior = functionChoiceBehavior
      } else if (typeof functionChoiceBehavior === 'object') {
        this.functionChoiceBehavior = FunctionChoiceBehavior.fromDict(functionChoiceBehavior)
      }
    }

    // Merge kwargs into extensionData
    this.extensionData = { ...extensionData, ...kwargs }

    // Unpack extension data into properties
    this.unpackExtensionData()
  }

  /**
   * Get the keys of the prompt execution settings.
   */
  get keys(): string[] {
    return Object.keys(this)
  }

  /**
   * Prepare the settings as a dictionary for sending to the AI service.
   *
   * By default, this method excludes the serviceId and extensionData fields,
   * as well as any fields that are null or undefined.
   *
   * @param kwargs - Additional options
   * @returns The prepared settings dictionary
   */
  prepareSettingsDict(kwargs?: Record<string, any>): Record<string, any> {
    const result: Record<string, any> = {}
    const excludeKeys = new Set(['serviceId', 'extensionData', 'structuredJsonResponse', 'functionChoiceBehavior'])

    for (const [key, value] of Object.entries(this)) {
      if (excludeKeys.has(key)) {
        continue
      }
      if (value === null || value === undefined) {
        continue
      }
      result[key] = value
    }

    if (kwargs) {
      Object.assign(result, kwargs)
    }

    return result
  }

  /**
   * Update the prompt execution settings from another prompt execution settings object.
   *
   * @param config - The prompt execution settings to update from
   */
  updateFromPromptExecutionSettings(config: PromptExecutionSettings): void {
    if (config.serviceId !== undefined && config.serviceId !== null) {
      this.serviceId = config.serviceId
    }

    config.packExtensionData()
    Object.assign(this.extensionData, config.extensionData)
    this.unpackExtensionData()
  }

  /**
   * Create a prompt execution settings from another prompt execution settings object.
   *
   * @param config - The prompt execution settings to create from
   * @returns A new prompt execution settings instance
   */
  static fromPromptExecutionSettings<T extends PromptExecutionSettings>(
    this: new (...args: any[]) => T,
    config: PromptExecutionSettings
  ): T {
    config.packExtensionData()
    return new this({
      serviceId: config.serviceId,
      extensionData: config.extensionData,
      functionChoiceBehavior: config.functionChoiceBehavior,
    })
  }

  /**
   * Update the prompt execution settings from extension data.
   * Does not overwrite existing values with null or undefined.
   *
   * @protected
   */
  protected unpackExtensionData(): void {
    for (const [key, value] of Object.entries(this.extensionData)) {
      if (value === null || value === undefined) {
        continue
      }
      if (key in this || this.keys.includes(key)) {
        ;(this as any)[key] = value
      }
    }
  }

  /**
   * Update the extension data from the prompt execution settings.
   *
   * @protected
   */
  protected packExtensionData(): void {
    for (const key of Object.keys(this)) {
      if (key === 'serviceId' || key === 'extensionData' || key === 'functionChoiceBehavior') {
        continue
      }
      const value = (this as any)[key]
      if (value !== null && value !== undefined) {
        this.extensionData[key] = value
      }
    }
  }
}
