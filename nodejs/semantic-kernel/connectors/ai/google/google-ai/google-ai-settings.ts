/**
 * Google AI settings.
 *
 * The settings are first loaded from environment variables with
 * the prefix 'GOOGLE_AI_'.
 * If the environment variables are not found, the settings can
 * be loaded from a .env file with the encoding 'utf-8'.
 * If the settings are not found in the .env file, the settings
 * are ignored; however, validation will fail alerting that the
 * settings are missing.
 *
 * Required settings for prefix 'GOOGLE_AI_' are:
 * - gemini_model_id: string - The Gemini model ID for the Google AI service, i.e. gemini-1.5-pro
 *               This value can be found in the Google AI service deployment.
 *               (Env var GOOGLE_AI_GEMINI_MODEL_ID)
 * - embedding_model_id: string - The embedding model ID for the Google AI service, i.e. text-embedding-004
 *               This value can be found in the Google AI service deployment.
 *               (Env var GOOGLE_AI_EMBEDDING_MODEL_ID)
 * - api_key: string - The API key for the Google AI service deployment.
 *               This value can be found in the Google AI service deployment.
 *               (Env var GOOGLE_AI_API_KEY)
 * - cloud_project_id: string - The Google Cloud project ID.
 *               (Env var GOOGLE_AI_CLOUD_PROJECT_ID)
 * - cloud_region: string - The Google Cloud region.
 *               (Env var GOOGLE_AI_CLOUD_REGION)
 * - use_vertexai: boolean - Whether to use Vertex AI. If true, cloud_project_id and cloud_region must be provided.
 *               (Env var GOOGLE_AI_USE_VERTEXAI)
 */
export class GoogleAISettings {
  public static readonly ENV_PREFIX: string = 'GOOGLE_AI_'

  public geminiModelId?: string
  public embeddingModelId?: string
  public apiKey?: string
  public cloudProjectId?: string
  public cloudRegion?: string
  public useVertexAI: boolean = false

  constructor(config?: Partial<GoogleAISettings>) {
    if (config) {
      this.geminiModelId = config.geminiModelId
      this.embeddingModelId = config.embeddingModelId
      this.apiKey = config.apiKey
      this.cloudProjectId = config.cloudProjectId
      this.cloudRegion = config.cloudRegion
      this.useVertexAI = config.useVertexAI ?? false
    }
  }

  /**
   * Load settings from environment variables with the GOOGLE_AI_ prefix.
   */
  public static fromEnvironment(): GoogleAISettings {
    const settings = new GoogleAISettings()

    settings.geminiModelId = process.env.GOOGLE_AI_GEMINI_MODEL_ID
    settings.embeddingModelId = process.env.GOOGLE_AI_EMBEDDING_MODEL_ID
    settings.apiKey = process.env.GOOGLE_AI_API_KEY
    settings.cloudProjectId = process.env.GOOGLE_AI_CLOUD_PROJECT_ID
    settings.cloudRegion = process.env.GOOGLE_AI_CLOUD_REGION
    settings.useVertexAI = process.env.GOOGLE_AI_USE_VERTEXAI === 'true'

    return settings
  }

  /**
   * Validate that required settings are present based on the configuration.
   * @throws Error if validation fails
   */
  public validate(): void {
    const errors: string[] = []

    if (this.useVertexAI) {
      if (!this.cloudProjectId) {
        errors.push('cloud_project_id is required when use_vertexai is true')
      }
      if (!this.cloudRegion) {
        errors.push('cloud_region is required when use_vertexai is true')
      }
    } else {
      if (!this.apiKey) {
        errors.push('api_key is required when use_vertexai is false')
      }
    }

    if (errors.length > 0) {
      throw new Error(`GoogleAI settings validation failed:\n${errors.join('\n')}`)
    }
  }
}
