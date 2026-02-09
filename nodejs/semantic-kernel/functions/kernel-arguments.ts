import { PromptExecutionSettings } from '../connectors/ai/prompt-execution-settings'

const DEFAULT_SERVICE_NAME = 'default'

/**
 * The arguments sent to the KernelFunction.
 *
 * This is a Map-like class with the additional field for execution settings.
 * It extends Map to behave like a dictionary while adding execution settings support.
 */
export class KernelArguments extends Map<string, any> {
  /** The execution settings for the function invocation */
  executionSettings?: Record<string, PromptExecutionSettings>

  /**
   * Initializes a new instance of the KernelArguments class.
   *
   * @param options - Configuration options
   * @param options.settings - The settings for execution (single, array, or dictionary)
   * @param options.args - Additional arguments as key-value pairs
   */
  constructor(options?: {
    settings?: PromptExecutionSettings | PromptExecutionSettings[] | Record<string, PromptExecutionSettings>
    args?: Record<string, any>
  }) {
    super()

    // Initialize with provided args
    if (options?.args) {
      for (const [key, value] of Object.entries(options.args)) {
        this.set(key, value)
      }
    }

    // Process settings
    if (options?.settings) {
      const settings = options.settings
      let settingsDict: Record<string, PromptExecutionSettings> = {}

      if (Array.isArray(settings)) {
        // If list, use service_id as key
        for (const s of settings) {
          const serviceId = s.serviceId || DEFAULT_SERVICE_NAME
          settingsDict[serviceId] = s
        }
      } else if (settings instanceof PromptExecutionSettings) {
        // Single setting
        const serviceId = settings.serviceId || DEFAULT_SERVICE_NAME
        settingsDict[serviceId] = settings
      } else {
        // Already a dictionary
        settingsDict = settings
      }

      this.executionSettings = settingsDict
    }
  }

  /**
   * Returns true if the arguments have any values.
   */
  get hasValues(): boolean {
    const hasArguments = this.size > 0
    const hasExecutionSettings = this.executionSettings !== undefined && Object.keys(this.executionSettings).length > 0
    return hasArguments || hasExecutionSettings
  }

  /**
   * Merge this KernelArguments with another KernelArguments or object.
   * Creates a new KernelArguments instance with merged values.
   *
   * @param other - The other arguments to merge
   * @returns A new KernelArguments with merged values
   */
  merge(other: KernelArguments | Record<string, any>): KernelArguments {
    // Merge execution settings
    const newExecutionSettings = { ...(this.executionSettings || {}) }
    if (other instanceof KernelArguments && other.executionSettings) {
      Object.assign(newExecutionSettings, other.executionSettings)
    }

    // Create new args object
    const newArgs: Record<string, any> = {}

    // Add current values
    for (const [key, value] of this.entries()) {
      newArgs[key] = value
    }

    // Add other values
    if (other instanceof KernelArguments) {
      for (const [key, value] of other.entries()) {
        newArgs[key] = value
      }
    } else {
      Object.assign(newArgs, other)
    }

    return new KernelArguments({
      settings: newExecutionSettings,
      args: newArgs,
    })
  }

  /**
   * Merge another KernelArguments or object into this instance (in-place).
   *
   * @param other - The other arguments to merge
   * @returns This instance for chaining
   */
  mergeInPlace(other: KernelArguments | Record<string, any> | Map<string, any>): KernelArguments {
    // Merge dictionary values
    if (other instanceof KernelArguments || other instanceof Map) {
      for (const [key, value] of other.entries()) {
        this.set(key, value)
      }
    } else if (typeof other === 'object' && other !== null) {
      for (const [key, value] of Object.entries(other)) {
        this.set(key, value)
      }
    }

    // Merge execution settings
    if (other instanceof KernelArguments && other.executionSettings) {
      if (this.executionSettings) {
        Object.assign(this.executionSettings, other.executionSettings)
      } else {
        this.executionSettings = { ...other.executionSettings }
      }
    }

    return this
  }

  /**
   * Convert to a plain object.
   *
   * @returns Plain object representation
   */
  toObject(): Record<string, any> {
    const result: Record<string, any> = {}
    for (const [key, value] of this.entries()) {
      result[key] = value
    }
    return result
  }

  /**
   * Serialize the KernelArguments to a JSON string.
   *
   * @param includeExecutionSettings - Whether to include execution settings in the output
   * @returns JSON string representation
   */
  dumps(includeExecutionSettings: boolean = false): string {
    const data = this.toObject()

    if (includeExecutionSettings && this.executionSettings) {
      data.execution_settings = this.executionSettings
    }

    return JSON.stringify(data, (_key, value) => {
      // Handle objects with toJSON or specific serialization needs
      if (value && typeof value === 'object') {
        if (typeof value.toJSON === 'function') {
          return value.toJSON()
        }
        if (typeof value.prepareSettingsDict === 'function') {
          return value.prepareSettingsDict()
        }
      }
      return value
    })
  }

  /**
   * Create a KernelArguments from a plain object.
   *
   * @param obj - The object to convert
   * @param settings - Optional execution settings
   * @returns A new KernelArguments instance
   */
  static fromObject(
    obj: Record<string, any>,
    settings?: PromptExecutionSettings | PromptExecutionSettings[] | Record<string, PromptExecutionSettings>
  ): KernelArguments {
    return new KernelArguments({ args: obj, settings })
  }
}
