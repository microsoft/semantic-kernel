import { GoogleGenerativeAI } from '@google/generative-ai'
import { ServiceInitializationError } from '../../../../../exceptions/service-exceptions'
import { EmbeddingGeneratorBase } from '../../../embedding-generator-base'
import { PromptExecutionSettings } from '../../../prompt-execution-settings'
import { GoogleAIEmbeddingPromptExecutionSettings } from '../google-ai-prompt-execution-settings'
import { GoogleAISettings } from '../google-ai-settings'

// Google AI SDK types (adjust import based on actual SDK)
interface EmbedContentResponse {
  embeddings: Array<{
    values: number[]
  }>
}

interface EmbedContentConfig {
  output_dimensionality?: number
}

interface GoogleClient {
  aio: {
    models: {
      embed_content(params: {
        model: string
        contents: string[]
        config: EmbedContentConfig
      }): Promise<EmbedContentResponse>
    }
  }
}

/**
 * Google AI Text Embedding Service.
 * Provides text embedding generation capabilities using Google's embedding models.
 */
export class GoogleAITextEmbedding extends EmbeddingGeneratorBase {
  static readonly MODEL_PROVIDER_NAME = 'googleai'

  // Properties from GoogleAIBase pattern
  serviceSettings: GoogleAISettings
  client: any | null = null

  /**
   * Initialize the Google AI Text Embedding service.
   *
   * If no arguments are provided, the service will attempt to load the settings from the environment.
   * The following environment variables are used:
   * - GOOGLE_AI_EMBEDDING_MODEL_ID
   * - GOOGLE_AI_API_KEY
   * - GOOGLE_AI_CLOUD_PROJECT_ID
   * - GOOGLE_AI_CLOUD_REGION
   * - GOOGLE_AI_USE_VERTEXAI
   *
   * @param params - Configuration parameters
   * @param params.embeddingModelId - The embedding model ID (Optional)
   * @param params.apiKey - The API key (Optional)
   * @param params.projectId - The Google Cloud project ID (Optional)
   * @param params.region - The Google Cloud region (Optional)
   * @param params.useVertexAI - Whether to use Vertex AI (Optional)
   * @param params.serviceId - The service ID (Optional)
   * @param params.client - The Google AI Client to use (Optional)
   * @throws {ServiceInitializationError} If validation fails or required settings are missing
   */
  constructor(
    params: {
      embeddingModelId?: string | null
      apiKey?: string | null
      projectId?: string | null
      region?: string | null
      useVertexAI?: boolean | null
      serviceId?: string | null
      client?: GoogleClient | null
    } = {}
  ) {
    let googleAISettings: GoogleAISettings

    try {
      googleAISettings = new GoogleAISettings({
        embeddingModelId: params.embeddingModelId ?? undefined,
        apiKey: params.apiKey ?? undefined,
        cloudProjectId: params.projectId ?? undefined,
        cloudRegion: params.region ?? undefined,
        useVertexAI: params.useVertexAI ?? undefined,
      })
    } catch (error) {
      throw new ServiceInitializationError(
        `Failed to validate Google AI settings: ${error instanceof Error ? error.message : String(error)}`
      )
    }

    if (!googleAISettings.embeddingModelId) {
      throw new ServiceInitializationError('The Google AI embedding model ID is required.')
    }

    if (!params.client) {
      if (googleAISettings.useVertexAI && !googleAISettings.cloudProjectId) {
        throw new ServiceInitializationError('Project ID must be provided when useVertexAI is true.')
      }
      if (!googleAISettings.useVertexAI && !googleAISettings.apiKey) {
        throw new ServiceInitializationError('The API key is required when useVertexAI is false.')
      }
    }

    // Call parent constructor with aiModelId and serviceId
    super({
      aiModelId: googleAISettings.embeddingModelId!,
      serviceId: params.serviceId || googleAISettings.embeddingModelId,
    })

    // Initialize GoogleAI-specific properties
    this.serviceSettings = googleAISettings
    this.client = params.client ?? null
  }

  /**
   * Get the prompt execution settings class for this service.
   * @override
   */
  getPromptExecutionSettingsClass(): typeof GoogleAIEmbeddingPromptExecutionSettings {
    return GoogleAIEmbeddingPromptExecutionSettings
  }

  /**
   * Generate embeddings for the given texts.
   *
   * @param texts - The texts to generate embeddings for
   * @param settings - Settings for the request (Optional)
   * @returns A 2D array of embeddings
   * @override
   */
  async generateEmbeddings(texts: string[], settings?: PromptExecutionSettings): Promise<number[][]> {
    return await this.generateRawEmbeddings(texts, settings)
  }

  /**
   * Generate raw embeddings for the given texts.
   *
   * @param texts - The texts to generate embeddings for
   * @param settings - Settings for the request (Optional)
   * @returns A list of embedding vectors
   * @override
   */
  async generateRawEmbeddings(texts: string[], settings?: PromptExecutionSettings): Promise<number[][]> {
    let executionSettings: GoogleAIEmbeddingPromptExecutionSettings

    if (!settings) {
      executionSettings = new GoogleAIEmbeddingPromptExecutionSettings()
    } else if (!(settings instanceof GoogleAIEmbeddingPromptExecutionSettings)) {
      executionSettings = this.getPromptExecutionSettingsFromSettings(settings)
    } else {
      executionSettings = settings
    }

    if (!this.serviceSettings.embeddingModelId) {
      throw new ServiceInitializationError('The Google AI embedding model ID is required.')
    }

    const embedContent = async (client: GoogleClient): Promise<EmbedContentResponse> => {
      return await client.aio.models.embed_content({
        model: this.serviceSettings.embeddingModelId!,
        contents: texts,
        config: {
          output_dimensionality: executionSettings.outputDimensionality ?? undefined,
        },
      })
    }

    let response: EmbedContentResponse

    if (this.client) {
      response = await embedContent(this.client)
    } else if (this.serviceSettings.useVertexAI) {
      const client = this.createVertexAIClient()
      try {
        response = await embedContent(client)
      } finally {
        this.closeClient(client)
      }
    } else {
      const client = this.createAPIClient()
      try {
        response = await embedContent(client)
      } finally {
        this.closeClient(client)
      }
    }

    return response.embeddings.map((embedding) => embedding.values)
  }

  /**
   * Convert generic settings to Google AI specific settings.
   * Overrides the base class method to provide Google AI specific conversion.
   *
   * @param settings - Generic prompt execution settings
   * @returns Google AI specific settings
   * @override
   */
  getPromptExecutionSettingsFromSettings(settings: PromptExecutionSettings): GoogleAIEmbeddingPromptExecutionSettings {
    // Convert or validate settings to Google AI specific format
    if (settings instanceof GoogleAIEmbeddingPromptExecutionSettings) {
      return settings
    }

    // Create new Google AI settings from generic settings
    return new GoogleAIEmbeddingPromptExecutionSettings()
  }

  /**
   * Helper method to create a Vertex AI client.
   * Implements the client creation pattern from GoogleAIBase.
   *
   * @private
   */
  private createVertexAIClient(): GoogleClient {
    // Implementation would depend on the actual Google AI SDK
    // This is a placeholder matching the Python pattern
    throw new Error('createVertexAIClient must be implemented based on your SDK')
  }

  /**
   * Helper method to create an API key-based client.
   * Implements the client creation pattern from GoogleAIBase.
   * Creates a client using the GoogleGenerativeAI SDK with API key authentication.
   *
   * @private
   */
  private createAPIClient(): GoogleClient {
    if (!this.serviceSettings.apiKey) {
      throw new ServiceInitializationError('API key is required to create a client.')
    }

    if (!this.serviceSettings.embeddingModelId) {
      throw new ServiceInitializationError('Embedding model ID is required to create a client.')
    }

    const genAI = new GoogleGenerativeAI(this.serviceSettings.apiKey)
    const model = genAI.getGenerativeModel({ model: this.serviceSettings.embeddingModelId })

    // Wrap the Google Generative AI client to match our GoogleClient interface
    return {
      aio: {
        models: {
          embed_content: async (params: {
            model: string
            contents: string[]
            config: EmbedContentConfig
          }): Promise<EmbedContentResponse> => {
            // Use batchEmbedContents to embed multiple texts at once
            const requests = params.contents.map((text) => ({
              content: { role: 'user', parts: [{ text }] },
            }))

            const result = await model.batchEmbedContents({
              requests,
            })

            // Transform the response to match our expected format
            return {
              embeddings: result.embeddings.map((embedding) => ({
                values: embedding.values,
              })),
            }
          },
        },
      },
    }
  }

  /**
   * Helper method to close/cleanup a client.
   *
   * @param _client - The client to clean up
   * @private
   */
  private closeClient(_client: GoogleClient): void {
    // No cleanup needed for Google Generative AI SDK
    // The SDK uses HTTP requests and doesn't maintain persistent connections
    // that require explicit cleanup
  }
}
