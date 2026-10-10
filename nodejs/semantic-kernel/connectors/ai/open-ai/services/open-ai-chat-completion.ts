import OpenAI from 'openai'
import { OpenAIChatCompletionBase } from './open-ai-chat-completion-base'
import { OpenAIModelTypes } from './open-ai-model-types'

/**
 * Options for initializing an OpenAI chat completion service.
 */
export interface OpenAIChatCompletionOptions {
  /** OpenAI model name */
  aiModelId?: string
  /** Service ID tied to the execution settings */
  serviceId?: string
  /** The optional API key to use */
  apiKey?: string
  /** The optional org ID to use */
  orgId?: string
  /** The default headers mapping for HTTP requests */
  defaultHeaders?: Record<string, string>
  /** An existing OpenAI client to use */
  client?: OpenAI
  /** The base URL for the OpenAI API */
  baseURL?: string
  /** The role to use for 'instruction' messages */
  instructionRole?: string
}

/**
 * OpenAI chat completion service.
 */
export class OpenAIChatCompletion extends OpenAIChatCompletionBase {
  /**
   * Initialize an OpenAIChatCompletion service.
   *
   * @param options - Configuration options for the service
   */
  constructor(options: OpenAIChatCompletionOptions = {}) {
    const { aiModelId, serviceId, apiKey, orgId, defaultHeaders, client, baseURL, instructionRole } = options

    // Validate required parameters
    if (!client && !apiKey) {
      throw new Error('The OpenAI API key is required.')
    }
    if (!aiModelId && !client) {
      throw new Error('The OpenAI model ID is required.')
    }

    // Create or use existing client
    const openAIClient =
      client ||
      new OpenAI({
        apiKey: apiKey || process.env.OPENAI_API_KEY,
        organization: orgId || process.env.OPENAI_ORG_ID,
        baseURL: baseURL || process.env.OPENAI_BASE_URL,
        defaultHeaders: defaultHeaders,
      })

    // Initialize the base class
    super(openAIClient, aiModelId || '', serviceId, OpenAIModelTypes.CHAT)

    // Set properties
    if (instructionRole) {
      this.instructionRole = instructionRole
    }
  }

  /**
   * Initialize an OpenAI service from a dictionary of settings.
   *
   * @param settings - A dictionary of settings for the service
   * @returns A new OpenAIChatCompletion instance
   */
  static fromDict(settings: Record<string, any>): OpenAIChatCompletion {
    return new OpenAIChatCompletion({
      aiModelId: settings.aiModelId || settings.ai_model_id,
      serviceId: settings.serviceId || settings.service_id,
      defaultHeaders: settings.defaultHeaders || settings.default_headers,
      apiKey: settings.apiKey || settings.api_key,
      orgId: settings.orgId || settings.org_id,
      baseURL: settings.baseURL || settings.base_url,
      instructionRole: settings.instructionRole || settings.instruction_role,
    })
  }
}
