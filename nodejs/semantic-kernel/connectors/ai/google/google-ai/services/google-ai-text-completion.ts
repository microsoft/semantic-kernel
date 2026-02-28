import { GoogleGenerativeAI } from '@google/generative-ai'
import { StreamingTextContent } from '../../../../../contents/streaming-text-content'
import { TextContent } from '../../../../../contents/text-content'
import { ServiceInitializationError } from '../../../../../exceptions/service-exceptions'
import { CompletionUsage } from '../../../completion-usage'
import { PromptExecutionSettings } from '../../../prompt-execution-settings'
import { TextCompletionClientBase } from '../../../text-completion-client-base'
import { GoogleAITextPromptExecutionSettings } from '../google-ai-prompt-execution-settings'
import { GoogleAISettings } from '../google-ai-settings'

// Google AI SDK types (adjust import based on actual SDK)
interface GenerateContentResponse {
  candidates: Candidate[]
  prompt_feedback?: any
  usage_metadata?: {
    prompt_token_count?: number
    candidates_token_count?: number
  }
}

interface Candidate {
  index?: number
  content?: {
    parts?: Array<{ text?: string }>
  }
  finish_reason?: string
  safety_ratings?: any[]
  token_count?: number
}

interface GenerateContentConfig {
  [key: string]: any
}

interface GoogleClient {
  aio: {
    models: {
      generate_content(params: {
        model: string
        contents: string
        config: GenerateContentConfig
      }): Promise<GenerateContentResponse>

      generate_content_stream(params: {
        model: string
        contents: string
        config: GenerateContentConfig
      }): Promise<AsyncIterable<GenerateContentResponse>>
    }
  }
}

/**
 * Google AI Text Completion Client.
 * Provides text completion capabilities using Google's Gemini models.
 *
 * This class extends TextCompletionClientBase (for text completion functionality)
 * and incorporates GoogleAIBase pattern (for Google AI specific settings and client management).
 */
export class GoogleAITextCompletion extends TextCompletionClientBase {
  static readonly MODEL_PROVIDER_NAME = 'googleai'

  // Properties from GoogleAIBase pattern
  serviceSettings: GoogleAISettings
  client: any | null = null

  /**
   * Initialize the Google AI Text Completion Client.
   *
   * If no arguments are provided, the service will attempt to load the settings from the environment.
   * The following environment variables are used:
   * - GOOGLE_AI_GEMINI_MODEL_ID
   * - GOOGLE_AI_API_KEY
   * - GOOGLE_AI_CLOUD_PROJECT_ID
   * - GOOGLE_AI_CLOUD_REGION
   * - GOOGLE_AI_USE_VERTEXAI
   *
   * @param params - Configuration parameters
   * @param params.geminiModelId - The Gemini model ID (Optional)
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
      geminiModelId?: string | null
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
        geminiModelId: params.geminiModelId ?? undefined,
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

    if (!googleAISettings.geminiModelId) {
      throw new ServiceInitializationError('The Google AI Gemini model ID is required.')
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
    super({ aiModelId: googleAISettings.geminiModelId!, serviceId: params.serviceId || googleAISettings.geminiModelId })

    // Initialize GoogleAI-specific properties
    this.serviceSettings = googleAISettings
    this.client = params.client ?? null
  }

  // #region Overriding base class methods

  /**
   * Get the prompt execution settings class for this service.
   * @override
   */
  getPromptExecutionSettingsClass(): typeof GoogleAITextPromptExecutionSettings {
    return GoogleAITextPromptExecutionSettings
  }

  /**
   * Internal implementation for getting text contents.
   * This method is called by the base class's getTextContents() method.
   *
   * @param prompt - The input prompt text
   * @param settings - Execution settings for the request
   * @returns Array of text content responses
   * @protected
   * @override
   */
  protected async _innerGetTextContents(prompt: string, settings: PromptExecutionSettings): Promise<TextContent[]> {
    let executionSettings: GoogleAITextPromptExecutionSettings

    if (!(settings instanceof GoogleAITextPromptExecutionSettings)) {
      executionSettings = this.getPromptExecutionSettingsFromSettings(settings)
    } else {
      executionSettings = settings
    }

    if (!this.serviceSettings.geminiModelId) {
      throw new ServiceInitializationError('The Google AI Gemini model ID is required.')
    }

    const generateContent = async (client: GoogleClient): Promise<GenerateContentResponse> => {
      return await client.aio.models.generate_content({
        model: this.serviceSettings.geminiModelId!,
        contents: prompt,
        config: executionSettings.prepareSettingsDict() as GenerateContentConfig,
      })
    }

    let response: GenerateContentResponse

    if (this.client) {
      response = await generateContent(this.client)
    } else if (this.serviceSettings.useVertexAI) {
      const client = this.createVertexAIClient()
      try {
        response = await generateContent(client)
      } finally {
        // Clean up client if needed
        this.closeClient(client)
      }
    } else {
      const client = this.createAPIClient()
      try {
        response = await generateContent(client)
      } finally {
        // Clean up client if needed
        this.closeClient(client)
      }
    }

    return response.candidates.map((candidate) => this._createTextContent(response, candidate))
  }

  /**
   * Internal implementation for getting streaming text contents.
   * This method is called by the base class's getStreamingTextContents() method.
   *
   * @param prompt - The input prompt text
   * @param settings - Execution settings for the request
   * @returns Async generator yielding arrays of streaming text content
   * @protected
   * @override
   */
  protected async *_innerGetStreamingTextContents(
    prompt: string,
    settings: PromptExecutionSettings
  ): AsyncGenerator<StreamingTextContent[], void, unknown> {
    let executionSettings: GoogleAITextPromptExecutionSettings

    if (!(settings instanceof GoogleAITextPromptExecutionSettings)) {
      executionSettings = this.getPromptExecutionSettingsFromSettings(settings)
    } else {
      executionSettings = settings
    }

    if (!this.serviceSettings.geminiModelId) {
      throw new ServiceInitializationError('The Google AI Gemini model ID is required.')
    }

    const generateContentStream = async function* (
      this: GoogleAITextCompletion,
      client: GoogleClient
    ): AsyncGenerator<GenerateContentResponse, void, unknown> {
      const stream = await client.aio.models.generate_content_stream({
        model: this.serviceSettings.geminiModelId!,
        contents: prompt,
        config: executionSettings.prepareSettingsDict() as GenerateContentConfig,
      })

      for await (const chunk of stream) {
        yield chunk
      }
    }.bind(this)

    if (this.client) {
      for await (const chunk of generateContentStream(this.client)) {
        yield chunk.candidates.map((candidate) => this._createStreamingTextContent(chunk, candidate))
      }
    } else if (this.serviceSettings.useVertexAI) {
      const client = this.createVertexAIClient()
      try {
        for await (const chunk of generateContentStream(client)) {
          yield chunk.candidates.map((candidate) => this._createStreamingTextContent(chunk, candidate))
        }
      } finally {
        this.closeClient(client)
      }
    } else {
      const client = this.createAPIClient()
      try {
        for await (const chunk of generateContentStream(client)) {
          yield chunk.candidates.map((candidate) => this._createStreamingTextContent(chunk, candidate))
        }
      } finally {
        this.closeClient(client)
      }
    }
  }

  // #endregion

  // #region Helper methods

  /**
   * Create a text content object from a response and candidate.
   *
   * @param response - The response from the service
   * @param candidate - The candidate from the response
   * @returns A text content object
   * @private
   */
  private _createTextContent(response: GenerateContentResponse, candidate: Candidate): TextContent {
    const responseMetadata = {
      ...this._getMetadataFromResponse(response),
      ...this._getMetadataFromCandidate(candidate),
    }

    const text = candidate.content?.parts?.[0]?.text || ''

    return new TextContent({
      aiModelId: this.aiModelId,
      text,
      innerContent: response,
      metadata: responseMetadata,
    })
  }

  /**
   * Create a streaming text content object from a chunk and candidate.
   *
   * @param chunk - The response chunk from the service
   * @param candidate - The candidate from the chunk
   * @returns A streaming text content object
   * @private
   */
  private _createStreamingTextContent(chunk: GenerateContentResponse, candidate: Candidate): StreamingTextContent {
    const responseMetadata = {
      ...this._getMetadataFromResponse(chunk),
      ...this._getMetadataFromCandidate(candidate),
    }

    const text = candidate.content?.parts?.[0]?.text || ''
    const choiceIndex = candidate.index ?? 0

    return new StreamingTextContent({
      aiModelId: this.aiModelId,
      choiceIndex,
      text,
      innerContent: chunk,
      metadata: responseMetadata,
    })
  }

  /**
   * Extract metadata from a response object.
   *
   * @param response - The response from the service
   * @returns A dictionary containing metadata
   * @private
   */
  private _getMetadataFromResponse(response: GenerateContentResponse): Record<string, any> {
    return {
      prompt_feedback: response.prompt_feedback,
      usage: new CompletionUsage({
        promptTokens: response.usage_metadata?.prompt_token_count ?? undefined,
        completionTokens: response.usage_metadata?.candidates_token_count ?? undefined,
      }),
    }
  }

  /**
   * Extract metadata from a candidate object.
   *
   * @param candidate - The candidate from the response
   * @returns A dictionary containing metadata
   * @private
   */
  private _getMetadataFromCandidate(candidate: Candidate): Record<string, any> {
    return {
      index: candidate.index,
      finish_reason: candidate.finish_reason,
      safety_ratings: candidate.safety_ratings,
      token_count: candidate.token_count,
    }
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

    if (!this.serviceSettings.geminiModelId) {
      throw new ServiceInitializationError('Gemini model ID is required to create a client.')
    }

    const genAI = new GoogleGenerativeAI(this.serviceSettings.apiKey)
    const model = genAI.getGenerativeModel({ model: this.serviceSettings.geminiModelId })

    // Wrap the Google Generative AI client to match our GoogleClient interface
    return {
      aio: {
        models: {
          generate_content: async (params: {
            model: string
            contents: string
            config: GenerateContentConfig
          }): Promise<GenerateContentResponse> => {
            const result = await model.generateContent({
              contents: [{ role: 'user', parts: [{ text: params.contents }] }],
              generationConfig: params.config,
            } as any)
            const response = result.response
            return {
              candidates:
                response.candidates?.map((candidate) => ({
                  index: candidate.index,
                  content: candidate.content,
                  finish_reason: candidate.finishReason,
                  safety_ratings: candidate.safetyRatings,
                  token_count: undefined, // Not provided in SDK response
                })) || [],
              prompt_feedback: response.promptFeedback,
              usage_metadata: {
                prompt_token_count: response.usageMetadata?.promptTokenCount,
                candidates_token_count: response.usageMetadata?.candidatesTokenCount,
              },
            }
          },
          generate_content_stream: async (params: {
            model: string
            contents: string
            config: GenerateContentConfig
          }): Promise<AsyncIterable<GenerateContentResponse>> => {
            const result = await model.generateContentStream({
              contents: [{ role: 'user', parts: [{ text: params.contents }] }],
              generationConfig: params.config,
            } as any)

            async function* streamWrapper(): AsyncGenerator<GenerateContentResponse, void> {
              for await (const chunk of result.stream) {
                yield {
                  candidates:
                    chunk.candidates?.map((candidate) => ({
                      index: candidate.index,
                      content: candidate.content,
                      finish_reason: candidate.finishReason,
                      safety_ratings: candidate.safetyRatings,
                      token_count: undefined,
                    })) || [],
                  prompt_feedback: chunk.promptFeedback,
                  usage_metadata: {
                    prompt_token_count: chunk.usageMetadata?.promptTokenCount,
                    candidates_token_count: chunk.usageMetadata?.candidatesTokenCount,
                  },
                }
              }
            }

            return streamWrapper()
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

  /**
   * Convert generic settings to Google AI specific settings.
   * Overrides the base class method to provide Google AI specific conversion.
   *
   * @param settings - Generic prompt execution settings
   * @returns Google AI specific settings
   * @override
   */
  getPromptExecutionSettingsFromSettings(settings: PromptExecutionSettings): GoogleAITextPromptExecutionSettings {
    // Convert or validate settings to Google AI specific format
    if (settings instanceof GoogleAITextPromptExecutionSettings) {
      return settings
    }

    // Create new Google AI settings from generic settings
    return new GoogleAITextPromptExecutionSettings()
  }

  // #endregion
}
