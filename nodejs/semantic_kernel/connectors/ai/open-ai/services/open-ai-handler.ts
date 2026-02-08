import type OpenAI from 'openai'
import type { Stream } from 'openai/streaming'
import { KernelJsonSchemaBuilder } from '../../../../schema/kernel-json-schema-builder'
import { generateStructuredOutputResponseFormatSchema } from '../../../utils/structured-output-schema'
import { OpenAIModelTypes } from './open-ai-model-types'

/**
 * Response type union for OpenAI API responses.
 */
export type OpenAIResponse =
  | OpenAI.Chat.ChatCompletion
  | OpenAI.Completion
  | Stream<OpenAI.Chat.Completions.ChatCompletionChunk>
  | Stream<OpenAI.Completions.Completion>
  | number[][]
  | OpenAI.Images.ImagesResponse
  | OpenAI.Audio.Transcription
  | Response

/**
 * Base prompt execution settings interface.
 */
export interface PromptExecutionSettings {
  prepareSettingsDict(): Record<string, any>
}

/**
 * OpenAI prompt execution settings interface.
 */
export interface OpenAIPromptExecutionSettings extends PromptExecutionSettings {
  prepareSettingsDict(): Record<string, any>
}

/**
 * OpenAI chat prompt execution settings interface.
 */
export interface OpenAIChatPromptExecutionSettings extends OpenAIPromptExecutionSettings {
  responseFormat?: any
  structuredJsonResponse?: boolean
  tools?: any[]
  parallelToolCalls?: boolean
}

/**
 * OpenAI embedding prompt execution settings interface.
 */
export interface OpenAIEmbeddingPromptExecutionSettings extends PromptExecutionSettings {
  prepareSettingsDict(): Record<string, any>
}

/**
 * OpenAI text to image execution settings interface.
 */
export interface OpenAITextToImageExecutionSettings extends PromptExecutionSettings {
  prepareSettingsDict(): Record<string, any>
}

/**
 * OpenAI audio to text execution settings interface.
 */
export interface OpenAIAudioToTextExecutionSettings extends PromptExecutionSettings {
  filename?: string
  prepareSettingsDict(): Record<string, any>
}

/**
 * OpenAI text to audio execution settings interface.
 */
export interface OpenAITextToAudioExecutionSettings extends PromptExecutionSettings {
  prepareSettingsDict(): Record<string, any>
}

/**
 * Internal class for calls to OpenAI API's.
 */
export abstract class OpenAIHandler {
  client: OpenAI
  aiModelType: OpenAIModelTypes = OpenAIModelTypes.CHAT
  promptTokens: number = 0
  completionTokens: number = 0
  totalTokens: number = 0

  constructor(client: OpenAI, aiModelType: OpenAIModelTypes = OpenAIModelTypes.CHAT) {
    this.client = client
    this.aiModelType = aiModelType
  }

  /**
   * Send a request to the OpenAI API.
   *
   * @param settings - The prompt execution settings
   * @returns The response from the OpenAI API
   */
  protected async sendRequest(settings: PromptExecutionSettings): Promise<OpenAIResponse> {
    if (this.aiModelType === OpenAIModelTypes.TEXT || this.aiModelType === OpenAIModelTypes.CHAT) {
      return await this.sendCompletionRequest(settings as OpenAIPromptExecutionSettings)
    }

    if (this.aiModelType === OpenAIModelTypes.EMBEDDING) {
      return await this.sendEmbeddingRequest(settings as OpenAIEmbeddingPromptExecutionSettings)
    }

    if (this.aiModelType === OpenAIModelTypes.TEXT_TO_IMAGE) {
      return await this.sendTextToImageRequest(settings as OpenAITextToImageExecutionSettings)
    }

    if (this.aiModelType === OpenAIModelTypes.AUDIO_TO_TEXT) {
      return await this.sendAudioToTextRequest(settings as OpenAIAudioToTextExecutionSettings)
    }

    if (this.aiModelType === OpenAIModelTypes.TEXT_TO_AUDIO) {
      return await this.sendTextToAudioRequest(settings as OpenAITextToAudioExecutionSettings)
    }

    throw new Error(`Model type ${this.aiModelType} is not supported`)
  }

  /**
   * Execute the appropriate call to OpenAI models.
   *
   * @param settings - The prompt execution settings
   * @returns The completion response
   */
  protected async sendCompletionRequest(
    settings: OpenAIPromptExecutionSettings
  ): Promise<
    | OpenAI.Chat.ChatCompletion
    | OpenAI.Completion
    | Stream<OpenAI.Chat.Completions.ChatCompletionChunk>
    | Stream<OpenAI.Completions.Completion>
  > {
    try {
      const settingsDict = settings.prepareSettingsDict()

      if (this.aiModelType === OpenAIModelTypes.CHAT) {
        const chatSettings = settings as OpenAIChatPromptExecutionSettings
        this.handleStructuredOutput(chatSettings, settingsDict)

        if (chatSettings.tools === null || chatSettings.tools === undefined) {
          delete settingsDict.parallelToolCalls
        }

        const response = await this.client.chat.completions.create(settingsDict as any)
        this.storeUsage(response)
        return response
      } else {
        const response = await this.client.completions.create(settingsDict as any)
        this.storeUsage(response)
        return response
      }
    } catch (error: any) {
      if (error.code === 'content_filter') {
        throw new Error(`${this.constructor.name} service encountered a content error: ${error.message}`, {
          cause: error,
        })
      }
      throw new Error(`${this.constructor.name} service failed to complete the prompt: ${error.message}`, {
        cause: error,
      })
    }
  }

  /**
   * Send a request to the OpenAI embeddings endpoint.
   *
   * @param settings - The embedding execution settings
   * @returns Array of embeddings
   */
  protected async sendEmbeddingRequest(settings: OpenAIEmbeddingPromptExecutionSettings): Promise<number[][]> {
    try {
      const response = await this.client.embeddings.create(settings.prepareSettingsDict() as any)

      this.storeUsage(response)
      return response.data.map((item) => item.embedding)
    } catch (error: any) {
      throw new Error(`${this.constructor.name} service failed to generate embeddings: ${error.message}`, {
        cause: error,
      })
    }
  }

  /**
   * Send a request to the OpenAI text to image endpoint.
   *
   * @param settings - The text to image execution settings
   * @returns The images response
   */
  protected async sendTextToImageRequest(
    settings: OpenAITextToImageExecutionSettings
  ): Promise<OpenAI.Images.ImagesResponse> {
    try {
      const response = await this.client.images.generate(settings.prepareSettingsDict() as any)
      this.storeUsage(response)
      return response
    } catch (error: any) {
      throw new Error(`Failed to generate image: ${error.message}`, { cause: error })
    }
  }

  /**
   * Send a request to the OpenAI image edit endpoint.
   *
   * @param image - The image file to edit
   * @param settings - Image edit execution settings
   * @param mask - Optional mask image
   * @returns The images response
   */
  protected async sendImageEditRequest(
    image: File | Blob,
    settings: OpenAITextToImageExecutionSettings,
    mask?: File | Blob
  ): Promise<OpenAI.Images.ImagesResponse> {
    try {
      const params: any = {
        image,
        ...settings.prepareSettingsDict(),
      }

      if (mask) {
        params.mask = mask
      }

      const response = await this.client.images.edit(params)
      this.storeUsage(response)
      return response
    } catch (error: any) {
      throw new Error(`Failed to edit image: ${error.message}`, { cause: error })
    }
  }

  /**
   * Send a request to the OpenAI audio to text endpoint.
   *
   * @param settings - The audio to text execution settings
   * @returns The transcription response
   */
  protected async sendAudioToTextRequest(
    settings: OpenAIAudioToTextExecutionSettings
  ): Promise<OpenAI.Audio.Transcription> {
    if (!settings.filename) {
      throw new Error('Audio file is required for audio to text service')
    }

    try {
      // In Node.js, we would read the file
      // This is a simplified version - actual implementation would depend on environment
      const fileContent = await this.readAudioFile(settings.filename)

      const response = await this.client.audio.transcriptions.create({
        file: fileContent,
        ...settings.prepareSettingsDict(),
      } as any)

      return response
    } catch (error: any) {
      throw new Error(`${this.constructor.name} service failed to transcribe audio: ${error.message}`, { cause: error })
    }
  }

  /**
   * Send a request to the OpenAI text to audio endpoint.
   *
   * @param settings - The text to audio execution settings
   * @returns The audio response content
   */
  protected async sendTextToAudioRequest(settings: OpenAITextToAudioExecutionSettings): Promise<Response> {
    try {
      const response = await this.client.audio.speech.create(settings.prepareSettingsDict() as any)
      return response as unknown as Response
    } catch (error: any) {
      throw new Error(`${this.constructor.name} service failed to generate audio: ${error.message}`, { cause: error })
    }
  }

  /**
   * Handle structured output for chat completions.
   *
   * @param requestSettings - The chat prompt execution settings
   * @param settings - The settings dictionary to modify
   */
  protected handleStructuredOutput(
    requestSettings: OpenAIChatPromptExecutionSettings,
    settings: Record<string, any>
  ): void {
    const responseFormat = requestSettings.responseFormat

    if (requestSettings.structuredJsonResponse && responseFormat) {
      // Case 1: response_format is a class/constructor with a schema
      if (typeof responseFormat === 'function' && this.hasSchema(responseFormat)) {
        // For classes with schemas (e.g., Zod schemas)
        settings.responseFormat = responseFormat
      }
      // Case 2: response_format is a type/class without built-in schema
      else if (typeof responseFormat === 'function') {
        const generatedSchema = KernelJsonSchemaBuilder.build(responseFormat, {
          structuredOutput: true,
        })

        if (generatedSchema) {
          settings.responseFormat = generateStructuredOutputResponseFormatSchema(responseFormat.name, generatedSchema)
        }
      }
      // Case 3: response_format is a dictionary, pass it without modification
      else if (typeof responseFormat === 'object' && responseFormat !== null) {
        settings.responseFormat = responseFormat
      }
    }
  }

  /**
   * Store the usage information from the response.
   *
   * @param response - The response from the OpenAI API
   */
  protected storeUsage(response: any): void {
    // Handle image responses
    if (response && 'created' in response && 'data' in response && response.usage) {
      // This is likely an ImagesResponse
      console.log(`OpenAI image usage: ${JSON.stringify(response.usage)}`)
      if (response.usage.input_tokens !== undefined) {
        this.promptTokens += response.usage.input_tokens
      }
      if (response.usage.total_tokens !== undefined) {
        this.totalTokens += response.usage.total_tokens
      }
      if (response.usage.output_tokens !== undefined) {
        this.completionTokens += response.usage.output_tokens
      }
      return
    }

    // Handle regular completion responses
    if (response && response.usage && !this.isStream(response)) {
      console.log(`OpenAI usage: ${JSON.stringify(response.usage)}`)

      if (response.usage.prompt_tokens !== undefined) {
        this.promptTokens += response.usage.prompt_tokens
      }
      if (response.usage.total_tokens !== undefined) {
        this.totalTokens += response.usage.total_tokens
      }
      if (response.usage.completion_tokens !== undefined) {
        this.completionTokens += response.usage.completion_tokens
      }
    }
  }

  /**
   * Check if a value is a stream.
   *
   * @private
   */
  private isStream(value: any): boolean {
    return (
      value &&
      typeof value === 'object' &&
      (typeof value[Symbol.asyncIterator] === 'function' || typeof value.getReader === 'function')
    )
  }

  /**
   * Check if a type has a schema method or property.
   *
   * @private
   */
  private hasSchema(value: any): boolean {
    return typeof value === 'function' && (value.schema !== undefined || value.prototype?.schema !== undefined)
  }

  /**
   * Read an audio file. This should be implemented based on the environment (Node.js vs browser).
   *
   * @private
   */
  private async readAudioFile(_filename: string): Promise<File> {
    // This is a placeholder - actual implementation would depend on the environment
    // In Node.js, you would use fs.readFile
    // In browser, you would handle File objects differently
    throw new Error('readAudioFile must be implemented in a concrete subclass')
  }
}
