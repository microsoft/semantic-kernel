/**
 * Minimal prompt execution settings interface.
 */
export interface PromptExecutionSettings {
  [key: string]: any
}

/**
 * Base class for all AI Services.
 *
 * Has an aiModelId and serviceId, any other fields have to be defined by the subclasses.
 *
 * The aiModelId can refer to a specific model, like 'gpt-35-turbo' for OpenAI,
 * or can just be a string that is used to identify the model in the service.
 *
 * The serviceId is used in Semantic Kernel to identify the service, if empty the aiModelId is used.
 */
export abstract class AIServiceClientBase {
  aiModelId: string
  serviceId: string

  constructor(options: { aiModelId: string; serviceId?: string }) {
    const { aiModelId, serviceId } = options

    // Validate and strip whitespace
    const trimmedModelId = aiModelId.trim()
    if (!trimmedModelId || trimmedModelId.length === 0) {
      throw new Error('aiModelId must be a non-empty string')
    }

    this.aiModelId = trimmedModelId
    this.serviceId = serviceId || trimmedModelId
  }

  /**
   * Get the request settings class.
   * Override this in subclass to return the proper prompt execution type the service is expecting.
   *
   * @returns The prompt execution settings constructor
   */
  getPromptExecutionSettingsClass(): new (...args: any[]) => PromptExecutionSettings {
    return class DefaultPromptExecutionSettings implements PromptExecutionSettings {
      [key: string]: any

      constructor(options?: Record<string, any>) {
        if (options) {
          Object.assign(this, options)
        }
      }
    }
  }

  /**
   * Create a request settings object.
   * All arguments are passed to the constructor of the request settings object.
   *
   * @param options - Options to pass to the settings constructor
   * @returns A new prompt execution settings instance
   */
  instantiatePromptExecutionSettings(options?: Record<string, any>): PromptExecutionSettings {
    const SettingsClass = this.getPromptExecutionSettingsClass()
    return new SettingsClass(options)
  }

  /**
   * Get the request settings from a settings object.
   *
   * @param settings - The settings object
   * @returns The converted or original settings
   */
  getPromptExecutionSettingsFromSettings(settings: PromptExecutionSettings): PromptExecutionSettings {
    const PromptExecutionSettingsType = this.getPromptExecutionSettingsClass()

    if (settings instanceof PromptExecutionSettingsType) {
      return settings
    }

    // If there's a static fromPromptExecutionSettings method, use it
    if (typeof (PromptExecutionSettingsType as any).fromPromptExecutionSettings === 'function') {
      return (PromptExecutionSettingsType as any).fromPromptExecutionSettings(settings)
    }

    // Otherwise, create a new instance with the settings
    return new PromptExecutionSettingsType(settings)
  }

  /**
   * Get the URL of the service.
   * Override this in the subclass to return the proper URL.
   * If the service does not have a URL, return null.
   *
   * @returns The service URL or null
   */
  serviceUrl(): string | null {
    return null
  }
}
