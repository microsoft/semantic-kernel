import OpenAI from 'openai'
import type {
  Assistant,
  AssistantCreateParams,
  AssistantTool,
  CodeInterpreterTool,
  FileSearchTool,
} from 'openai/resources/beta/index'
import type { MessageCreateParams } from 'openai/resources/beta/threads/messages'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import {
  AgentInitializationException,
  AgentInvokeException,
  AgentThreadOperationException,
} from '../../exceptions/agent-exceptions'
import { Kernel } from '../../kernel'
import { createDefaultLogger, Logger } from '../../utils/logger'
import { Agent, AgentResponseItem, AgentSpec, AgentThread, IntermediateMessageCallback, ToolSpec } from '../agent'
import { AssistantThreadActions, DEFAULT_RUN_POLLING_OPTIONS, RunPollingOptions } from './assistant-thread-actions'

// Re-export types and constants from assistant-thread-actions for external consumers
export { AssistantThreadActions, DEFAULT_RUN_POLLING_OPTIONS } from './assistant-thread-actions'
export type { FunctionActionResult, RunPollingOptions } from './assistant-thread-actions'

const logger: Logger = createDefaultLogger('OpenAIAssistantAgent')

/**
 * Tool builder function type.
 * Takes a tool spec and optional kernel, returns tools array and resources object.
 */
type ToolBuilder = (spec: ToolSpec, kernel?: Kernel) => [AssistantTool[], AssistantCreateParams.ToolResources]

/**
 * Registry of tool builders keyed by tool type.
 */
const TOOL_BUILDERS: Map<string, ToolBuilder> = new Map()

/**
 * Register a tool builder for a specific tool type.
 */
function registerTool(toolType: string, builder: ToolBuilder): void {
  TOOL_BUILDERS.set(toolType.toLowerCase(), builder)
}

/**
 * Build a tool from a tool spec.
 */
function buildTool(spec: ToolSpec, kernel?: Kernel): [AssistantTool[], AssistantCreateParams.ToolResources] {
  if (!spec.type) {
    throw new Error('Tool spec must include a "type" field.')
  }

  const builder = TOOL_BUILDERS.get(spec.type.toLowerCase())
  if (!builder) {
    throw new AgentInitializationException(`Unsupported tool type: ${spec.type}`)
  }

  return builder(spec, kernel)
}

// Register built-in tool builders
registerTool('code_interpreter', (spec: ToolSpec) => {
  const fileIds = spec.options?.file_ids
  return OpenAIAssistantAgent.configureCodeInterpreterTool({ fileIds })
})

registerTool('file_search', (spec: ToolSpec) => {
  const vectorStoreIds = spec.options?.vector_store_ids
  if (!vectorStoreIds || !Array.isArray(vectorStoreIds) || vectorStoreIds.length === 0) {
    logger.error(`Missing or malformed 'vector_store_ids' in tool spec: ${JSON.stringify(spec)}`)

    throw new AgentInitializationException(
      `Missing or malformed 'vector_store_ids' in tool spec: ${JSON.stringify(spec)}`
    )
  }
  return OpenAIAssistantAgent.configureFileSearchTool({ vectorStoreIds })
})

/**
 * OpenAI Assistant Agent Thread class.
 *
 * Note: This class is marked as 'release_candidate' and may change in the future.
 */
export class AssistantAgentThread extends AgentThread {
  protected _client: OpenAI
  protected _messages?: MessageCreateParams[]
  protected _metadata?: Record<string, string>
  protected _toolResources?: AssistantCreateParams.ToolResources

  constructor(options: {
    client: OpenAI
    threadId?: string
    messages?: MessageCreateParams[]
    metadata?: Record<string, string>
    toolResources?: AssistantCreateParams.ToolResources
  }) {
    super()

    if (!options.client) {
      throw new AgentInitializationException('Client cannot be null')
    }

    this._client = options.client
    this._id = options.threadId
    this._messages = options.messages
    this._metadata = options.metadata
    this._toolResources = options.toolResources
  }

  /**
   * Starts the thread and returns its ID.
   */
  protected async _create(): Promise<string> {
    try {
      const response = await this._client.beta.threads.create({
        messages: this._messages,
        metadata: this._metadata,
        tool_resources: this._toolResources,
      })
      return response.id
    } catch (error) {
      logger.error('Failed to create thread:', error)

      throw new AgentThreadOperationException(
        'The thread could not be created due to an error response from the service.'
      )
    }
  }

  /**
   * Ends the current thread.
   */
  protected async _delete(): Promise<void> {
    if (!this._id) {
      throw new AgentThreadOperationException('The thread cannot be deleted because it has not been created yet.')
    }
    try {
      await this._client.beta.threads.del(this._id)
    } catch (error) {
      logger.error('Failed to delete thread:', error)

      throw new AgentThreadOperationException(
        'The thread could not be deleted due to an error response from the service.'
      )
    }
  }

  /**
   * Called when a new message has been contributed to the chat.
   */
  protected async _onNewMessage(newMessage: string | ChatMessageContent): Promise<void> {
    if (!this._id) {
      throw new AgentThreadOperationException('Thread ID is not set')
    }

    // Use AssistantThreadActions to create the message
    await AssistantThreadActions.createMessage(this._client, this._id, newMessage)
  }

  /**
   * Get the messages in the thread.
   */
  async *getMessages(sortOrder?: 'asc' | 'desc'): AsyncIterable<ChatMessageContent> {
    if (this._isDeleted) {
      throw new AgentThreadOperationException('The thread has been deleted.')
    }
    if (!this._id) {
      await this.create()
    }
    if (!this._id) {
      throw new AgentThreadOperationException('Thread ID is not available')
    }

    yield* AssistantThreadActions.getMessages(this._client, this._id, sortOrder)
  }
}

/**
 * Run-level parameters for OpenAI Assistant invocations.
 */
export interface RunLevelParameters {
  /**
   * Additional instructions to append to the assistant's instructions.
   */
  additionalInstructions?: string

  /**
   * Additional messages to add to the thread before running.
   */
  additionalMessages?: ChatMessageContent[]

  /**
   * Maximum number of completion tokens to generate.
   */
  maxCompletionTokens?: number

  /**
   * Maximum number of prompt tokens to use.
   */
  maxPromptTokens?: number

  /**
   * Metadata to attach to the run.
   */
  metadata?: Record<string, string>

  /**
   * Model override for this specific run.
   */
  model?: string

  /**
   * Whether to enable parallel tool calls.
   */
  parallelToolCalls?: boolean

  /**
   * Reasoning effort level (for reasoning models).
   */
  reasoningEffort?: 'low' | 'medium' | 'high'

  /**
   * Response format configuration.
   */
  responseFormat?: any

  /**
   * Tools to use for this specific run.
   */
  tools?: AssistantTool[]

  /**
   * Sampling temperature (0-2).
   */
  temperature?: number

  /**
   * Nucleus sampling threshold (0-1).
   */
  topP?: number

  /**
   * Truncation strategy for the thread.
   */
  truncationStrategy?: any

  /**
   * Run-level polling options.
   */
  pollingOptions?: RunPollingOptions
}

/**
 * OpenAI Assistant Agent class.
 *
 * Provides the ability to interact with OpenAI Assistants.
 *
 * Note: This class is marked as 'release_candidate' and may change in the future.
 */
export class OpenAIAssistantAgent extends Agent {
  client: OpenAI
  definition: Assistant
  plugins: any[] = []
  pollingOptions: RunPollingOptions = DEFAULT_RUN_POLLING_OPTIONS

  constructor(options: {
    client: OpenAI
    definition: Assistant
    kernel?: Kernel
    plugins?: any[]
    pollingOptions?: RunPollingOptions
    name?: string
    description?: string
    id?: string
    instructions?: string
  }) {
    const name = options.name || options.definition.name || `assistant_agent_${Math.random().toString(36).substring(7)}`
    const description = options.description || options.definition.description

    super({
      name,
      description: description || '',
      kernel: options.kernel,
      id: options.id || options.definition.id,
    })

    this.client = options.client
    this.definition = options.definition

    if (options.plugins) {
      this.plugins = options.plugins
    }

    if (options.pollingOptions) {
      this.pollingOptions = { ...this.pollingOptions, ...options.pollingOptions }
    }

    if (options.instructions) {
      this.instructions = options.instructions
    } else if (options.definition.instructions) {
      this.instructions = options.definition.instructions
    }
  }

  /**
   * Resolve placeholders in a YAML string.
   *
   * Substitutes placeholders in the format ${Category:Key} with actual values
   * from settings or extras objects.
   *
   * @param options - Configuration options
   * @param options.yamlStr - YAML string containing placeholders
   * @param options.settings - Settings object organized by category (e.g., { OpenAI: { Key: 'sk-...' } })
   * @param options.extras - Additional key-value pairs for substitution
   * @returns YAML string with placeholders resolved
   *
   * @example
   * ```typescript
   * const yaml = `
   * api_key: \${OpenAI:Key}
   * model: \${OpenAI:Model}
   * `
   *
   * const resolved = OpenAIAssistantAgent.resolvePlaceholders({
   *   yamlStr: yaml,
   *   settings: {
   *     OpenAI: {
   *       Key: 'sk-1234567890',
   *       Model: 'gpt-4'
   *     }
   *   }
   * })
   * ```
   */
  static resolvePlaceholders(options: {
    yamlStr: string
    settings?: Record<string, any>
    extras?: Record<string, any>
  }): string {
    const { yamlStr, settings, extras } = options

    // Regex to match ${Category:Key} patterns
    const placeholderPattern = /\$\{([^:}]+):([^}]+)\}/g

    return yamlStr.replace(placeholderPattern, (match, category, key) => {
      // Try to get value from settings first
      if (settings && settings[category]) {
        const categorySettings = settings[category]
        if (categorySettings && typeof categorySettings === 'object' && key in categorySettings) {
          const value = categorySettings[key]
          // Handle various value types
          if (value === null || value === undefined) {
            return match // Keep placeholder if value is null/undefined
          }
          return String(value)
        }
      }

      // Try to get value from extras using combined key
      if (extras) {
        const combinedKey = `${category}:${key}`
        if (combinedKey in extras) {
          const value = extras[combinedKey]
          if (value === null || value === undefined) {
            return match // Keep placeholder if value is null/undefined
          }
          return String(value)
        }

        // Also try just the key without category
        if (key in extras) {
          const value = extras[key]
          if (value === null || value === undefined) {
            return match // Keep placeholder if value is null/undefined
          }
          return String(value)
        }
      }

      // If not found, return the original placeholder unchanged
      return match
    })
  }

  /**
   * Setup resources for the OpenAI Assistant Agent.
   *
   * Creates an OpenAI client and returns it along with the model ID.
   *
   * @param options - Configuration options
   * @param options.aiModelId - The AI model ID (required)
   * @param options.apiKey - The OpenAI API key (can also be set via OPENAI_API_KEY env var)
   * @param options.orgId - The OpenAI organization ID (optional)
   * @param options.defaultHeaders - Additional headers to include in requests (optional)
   * @param options.baseURL - Custom base URL for API requests (optional)
   * @returns A tuple of [OpenAI client, model ID]
   * @throws AgentInitializationException if API key or model ID is not provided
   *
   * @example
   * ```typescript
   * const [client, modelId] = OpenAIAssistantAgent.setupResources({
   *   aiModelId: 'gpt-4',
   *   apiKey: process.env.OPENAI_API_KEY
   * })
   * ```
   */
  static setupResources(options: {
    aiModelId?: string
    apiKey?: string
    orgId?: string
    defaultHeaders?: Record<string, string>
    baseURL?: string
  }): [OpenAI, string] {
    if (!options.aiModelId) {
      throw new AgentInitializationException('The OpenAI model ID is required.')
    }

    const client = OpenAIAssistantAgent.createClient({
      apiKey: options.apiKey,
      orgId: options.orgId,
      defaultHeaders: options.defaultHeaders,
      baseURL: options.baseURL,
    })

    return [client, options.aiModelId]
  }

  /**
   * Create an OpenAI client.
   *
   * @param options - Configuration options for the OpenAI client
   * @param options.apiKey - The OpenAI API key (can also be set via OPENAI_API_KEY env var)
   * @param options.orgId - The OpenAI organization ID (optional)
   * @param options.defaultHeaders - Additional headers to include in requests (optional)
   * @param options.baseURL - Custom base URL for API requests (optional)
   * @returns An OpenAI client instance
   * @throws Error if API key is not provided
   *
   * @example
   * ```typescript
   * const client = OpenAIAssistantAgent.createClient({
   *   apiKey: process.env.OPENAI_API_KEY,
   *   orgId: process.env.OPENAI_ORG_ID
   * })
   * ```
   */
  static createClient(options: {
    apiKey?: string
    orgId?: string
    defaultHeaders?: Record<string, string>
    baseURL?: string
  }): OpenAI {
    // Get API key from options or environment variable
    const apiKey = options.apiKey || process.env.OPENAI_API_KEY

    if (!apiKey) {
      throw new AgentInitializationException(
        'The OpenAI API key is required. Provide it via options.apiKey or OPENAI_API_KEY environment variable.'
      )
    }

    // Merge headers with semantic kernel user agent
    const mergedHeaders: Record<string, string> = {
      'User-Agent': 'Semantic-Kernel',
      ...(options.defaultHeaders || {}),
    }

    // Prepend to existing user-agent if present
    if (options.defaultHeaders?.['User-Agent']) {
      mergedHeaders['User-Agent'] = `Semantic-Kernel ${options.defaultHeaders['User-Agent']}`
    }

    // Create and return actual OpenAI client instance
    return new OpenAI({
      apiKey,
      organization: options.orgId,
      defaultHeaders: mergedHeaders,
      baseURL: options.baseURL,
    })
  }

  /**
   * Configure code interpreter tool.
   */
  static configureCodeInterpreterTool(options?: {
    fileIds?: string[]
  }): [AssistantTool[], AssistantCreateParams.ToolResources] {
    const tools: CodeInterpreterTool[] = [{ type: 'code_interpreter' }]
    const resources: AssistantCreateParams.ToolResources = {}

    if (options?.fileIds && options.fileIds.length > 0) {
      resources.code_interpreter = { file_ids: options.fileIds }
    }

    return [tools, resources]
  }

  /**
   * Configure file search tool.
   */
  static configureFileSearchTool(options: {
    vectorStoreIds: string[]
  }): [AssistantTool[], AssistantCreateParams.ToolResources] {
    if (!options.vectorStoreIds || options.vectorStoreIds.length === 0) {
      throw new AgentInitializationException('vectorStoreIds is required for file search tool')
    }

    const tools: FileSearchTool[] = [{ type: 'file_search' }]
    const resources: AssistantCreateParams.ToolResources = {
      file_search: { vector_store_ids: options.vectorStoreIds },
    }

    return [tools, resources]
  }

  /**
   * Configure response format for structured outputs.
   *
   * Supports different response format types for OpenAI Assistants:
   * - 'text': Default text response (no structured output)
   * - 'json_object': Enable JSON mode (assistant returns valid JSON)
   * - 'json_schema': Structured outputs with JSON schema validation
   *
   * @param options - Configuration options
   * @param options.type - The response format type ('text', 'json_object', or 'json_schema')
   * @param options.jsonSchema - JSON schema definition (required when type is 'json_schema')
   * @param options.jsonSchema.name - Name for the schema
   * @param options.jsonSchema.schema - The JSON schema object
   * @param options.jsonSchema.strict - Whether to enforce strict schema validation (default: true)
   * @returns Response format configuration object
   *
   * @example
   * ```typescript
   * // Enable JSON mode
   * const jsonFormat = OpenAIAssistantAgent.configureResponseFormat({
   *   type: 'json_object'
   * })
   *
   * // Use JSON schema for structured outputs
   * const schemaFormat = OpenAIAssistantAgent.configureResponseFormat({
   *   type: 'json_schema',
   *   jsonSchema: {
   *     name: 'UserInfo',
   *     schema: {
   *       type: 'object',
   *       properties: {
   *         name: { type: 'string' },
   *         age: { type: 'number' }
   *       },
   *       required: ['name', 'age']
   *     },
   *     strict: true
   *   }
   * })
   * ```
   */
  static configureResponseFormat(options: {
    type: 'text' | 'json_object' | 'json_schema'
    jsonSchema?: {
      name: string
      schema: Record<string, any>
      strict?: boolean
      description?: string
    }
  }): any {
    if (options.type === 'text') {
      return { type: 'text' }
    }

    if (options.type === 'json_object') {
      return { type: 'json_object' }
    }

    if (options.type === 'json_schema') {
      if (!options.jsonSchema) {
        throw new AgentInitializationException('jsonSchema is required when type is "json_schema"')
      }

      if (!options.jsonSchema.name) {
        throw new AgentInitializationException('jsonSchema.name is required')
      }

      if (!options.jsonSchema.schema) {
        throw new AgentInitializationException('jsonSchema.schema is required')
      }

      return {
        type: 'json_schema',
        json_schema: {
          name: options.jsonSchema.name,
          schema: options.jsonSchema.schema,
          strict: options.jsonSchema.strict ?? true,
          ...(options.jsonSchema.description && { description: options.jsonSchema.description }),
        },
      }
    }

    throw new AgentInitializationException(`Unsupported response format type: ${options.type}`)
  }

  /**
   * Get the channel keys for this agent.
   *
   * Channel keys are used to identify and route messages to the appropriate agent channel.
   * For OpenAI Assistant agents, this typically includes the class name and agent ID.
   *
   * @yields Channel key strings
   *
   * @example
   * ```typescript
   * for (const key of agent.getChannelKeys()) {
   *   logger.info('Channel key:', key)
   * }
   * ```
   */
  *getChannelKeys(): Iterable<string> {
    // Yield the class name
    yield this.constructor.name

    // Yield the agent ID
    if (this.id) {
      yield this.id
    }

    // Yield the agent name
    if (this.name) {
      yield this.name
    }

    // Yield the base URL to distinguish between different API endpoints
    if (this.client.baseURL) {
      yield String(this.client.baseURL)
    }
  }

  /**
   * Create a channel for this agent.
   *
   * Creates and returns an OpenAIAssistantChannel instance that can be used for
   * communication with this agent.
   *
   * @param options - Configuration options
   * @param options.threadId - Optional thread ID. If not provided, a new thread will be created.
   * @returns A promise that resolves to an OpenAIAssistantChannel instance
   *
   * @example
   * ```typescript
   * // Create channel with new thread
   * const channel = await agent.createChannel()
   *
   * // Create channel with existing thread
   * const channel = await agent.createChannel({ threadId: 'thread_abc123' })
   * ```
   */
  async createChannel(options?: { threadId?: string }): Promise<any> {
    const { OpenAIAssistantChannel } = await import('../channels/open-ai-assistant-channel.js')

    let threadId = options?.threadId

    // Create a new thread if no threadId provided
    if (!threadId) {
      const thread = new AssistantAgentThread({ client: this.client })
      await thread.create()
      threadId = thread.id!
    }

    return new OpenAIAssistantChannel({
      client: this.client,
      threadId,
    })
  }

  /**
   * Private helper method to prepare thread and add messages.
   *
   * @private
   */
  private async _prepareThread(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
  }): Promise<AssistantAgentThread> {
    // Ensure thread exists
    let assistantThread = options.thread as AssistantAgentThread | undefined
    if (!assistantThread) {
      assistantThread = new AssistantAgentThread({ client: this.client })
      await assistantThread.create()
    } else if (!assistantThread.id) {
      await assistantThread.create()
    }

    // Add messages to the thread if provided
    if (options.messages) {
      const messageArray = Array.isArray(options.messages) ? options.messages : [options.messages]
      for (const msg of messageArray) {
        const content = typeof msg === 'string' ? msg : msg.content
        await this.client.beta.threads.messages.create(assistantThread.id!, {
          role: 'user',
          content,
        })
      }
    }

    return assistantThread
  }

  /**
   * Get a response from the assistant.
   *
   * This method blocks until the final result is available and returns a single
   * AgentResponseItem containing the last message from the assistant.
   */
  async getResponse(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    instructionsOverride?: string
    additionalInstructions?: string
    additionalMessages?: ChatMessageContent[]
    maxCompletionTokens?: number
    maxPromptTokens?: number
    metadata?: Record<string, string>
    model?: string
    parallelToolCalls?: boolean
    reasoningEffort?: 'low' | 'medium' | 'high'
    responseFormat?: any
    tools?: any[]
    temperature?: number
    topP?: number
    truncationStrategy?: any
    pollingOptions?: RunPollingOptions
    [key: string]: any
  }): Promise<AgentResponseItem<ChatMessageContent>> {
    // Collect all response messages using invoke
    const responseMessages: ChatMessageContent[] = []
    for await (const responseItem of this.invoke(options)) {
      responseMessages.push(responseItem.message)
    }

    // Return the final message
    if (responseMessages.length === 0) {
      throw new AgentInvokeException('No response messages were returned from the agent.')
    }

    const finalMessage = responseMessages[responseMessages.length - 1]
    return new AgentResponseItem(finalMessage, responseMessages[0].metadata?.thread || options.thread)
  }

  /**
   * Invoke the assistant and get responses.
   */
  async *invoke(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    onIntermediateMessage?: IntermediateMessageCallback
    additionalInstructions?: string
    additionalMessages?: ChatMessageContent[]
    instructionsOverride?: string
    maxCompletionTokens?: number
    maxPromptTokens?: number
    metadata?: Record<string, string>
    model?: string
    parallelToolCalls?: boolean
    reasoningEffort?: 'low' | 'medium' | 'high'
    responseFormat?: any
    temperature?: number
    topP?: number
    truncationStrategy?: any
    pollingOptions?: RunPollingOptions
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
    // Prepare thread and add messages
    const assistantThread = await this._prepareThread(options)

    if (!assistantThread.id) {
      throw new AgentInvokeException('Thread ID is required for invocation')
    }

    // Delegate to AssistantThreadActions
    for await (const [isVisible, message] of AssistantThreadActions.invoke({
      agent: this,
      threadId: assistantThread.id,
      additionalInstructions: options.additionalInstructions,
      additionalMessages: options.additionalMessages,
      arguments: this.arguments,
      instructionsOverride: options.instructionsOverride,
      kernel: this.kernel,
      maxCompletionTokens: options.maxCompletionTokens,
      maxPromptTokens: options.maxPromptTokens,
      metadata: options.metadata,
      model: options.model,
      parallelToolCalls: options.parallelToolCalls,
      reasoningEffort: options.reasoningEffort,
      responseFormat: options.responseFormat,
      temperature: options.temperature,
      topP: options.topP,
      truncationStrategy: options.truncationStrategy,
      pollingOptions: options.pollingOptions || this.pollingOptions,
    })) {
      // Emit intermediate message if provided and visible
      if (isVisible && options.onIntermediateMessage) {
        await options.onIntermediateMessage(message)
      }

      // Always yield visible messages
      if (isVisible) {
        yield new AgentResponseItem(message, assistantThread)
      }
    }
  }

  /**
   * Invoke the assistant with streaming responses.
   *
   * This method returns streaming chunks of messages as they are generated,
   * yielding StreamingChatMessageContent objects.
   */
  async *invokeStream(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    onIntermediateMessage?: IntermediateMessageCallback
    additionalInstructions?: string
    additionalMessages?: ChatMessageContent[]
    instructionsOverride?: string
    maxCompletionTokens?: number
    maxPromptTokens?: number
    metadata?: Record<string, string>
    model?: string
    parallelToolCalls?: boolean
    reasoningEffort?: 'low' | 'medium' | 'high'
    responseFormat?: any
    temperature?: number
    topP?: number
    truncationStrategy?: any
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
    // Prepare thread and add messages
    const assistantThread = await this._prepareThread(options)

    if (!assistantThread.id) {
      throw new AgentInvokeException('Thread ID is required for invocation')
    }

    // Track output messages for intermediate callback
    const outputMessages: ChatMessageContent[] = []

    // Delegate to AssistantThreadActions
    for await (const streamingMessage of AssistantThreadActions.invokeStream({
      agent: this,
      threadId: assistantThread.id,
      additionalInstructions: options.additionalInstructions,
      additionalMessages: options.additionalMessages,
      arguments: this.arguments,
      instructionsOverride: options.instructionsOverride,
      kernel: this.kernel,
      maxCompletionTokens: options.maxCompletionTokens,
      maxPromptTokens: options.maxPromptTokens,
      metadata: options.metadata,
      model: options.model,
      outputMessages,
      parallelToolCalls: options.parallelToolCalls,
      reasoningEffort: options.reasoningEffort,
      responseFormat: options.responseFormat,
      temperature: options.temperature,
      topP: options.topP,
      truncationStrategy: options.truncationStrategy,
    })) {
      yield new AgentResponseItem(streamingMessage, assistantThread)
    }

    // Emit collected output messages via callback
    if (options.onIntermediateMessage && outputMessages.length > 0) {
      for (const msg of outputMessages) {
        await assistantThread.onNewMessage(msg)
        await options.onIntermediateMessage(msg)
      }
    }
  }

  /**
   * Create an assistant agent from a YAML specification.
   *
   * @param options - Configuration options
   * @param options.yamlContent - YAML string containing the agent specification
   * @param options.client - OpenAI client instance
   * @param options.kernel - Optional Kernel instance
   * @param options.settings - Settings object for placeholder resolution
   * @param options.extras - Additional key-value pairs for placeholder resolution
   * @returns A new OpenAIAssistantAgent instance
   *
   * @example
   * ```typescript
   * const yamlSpec = `
   * name: MyAssistant
   * description: A helpful assistant
   * model:
   *   id: \${OpenAI:Model}
   * instructions: You are a helpful assistant
   * `
   *
   * const agent = await OpenAIAssistantAgent.fromYaml({
   *   yamlContent: yamlSpec,
   *   client: openaiClient,
   *   settings: {
   *     OpenAI: {
   *       Model: 'gpt-4'
   *     }
   *   }
   * })
   * ```
   */
  static async fromYaml(options: {
    yamlContent: string
    client: OpenAI
    kernel?: Kernel
    settings?: Record<string, any>
    extras?: Record<string, any>
  }): Promise<OpenAIAssistantAgent> {
    // Resolve placeholders in YAML content
    let resolvedYaml = options.yamlContent
    if (options.settings || options.extras) {
      resolvedYaml = OpenAIAssistantAgent.resolvePlaceholders({
        yamlStr: options.yamlContent,
        settings: options.settings,
        extras: options.extras,
      })
    }

    // Parse YAML content to JavaScript object
    // Note: This requires a YAML parsing library like 'yaml' or 'js-yaml'
    // For now, we'll provide a basic implementation that expects the caller
    // to use a YAML parser externally, or we can add a dependency

    let data: Record<string, any>
    try {
      // Try to use the 'yaml' package if available
      // In production, you would: import * as yaml from 'yaml'
      // For now, we'll assume JSON format or throw an error
      data = JSON.parse(resolvedYaml)
    } catch (jsonError) {
      // If JSON parsing fails, throw a helpful error
      throw new AgentInitializationException(
        'fromYaml requires YAML content to be parsed. Please install a YAML parsing library ' +
          '(e.g., "yaml" or "js-yaml") and parse the YAML before calling fromDict, or provide JSON format. ' +
          `Parse error: ${jsonError}`
      )
    }

    // Delegate to fromDict
    return await OpenAIAssistantAgent.fromDict({
      data,
      client: options.client,
      kernel: options.kernel,
    })
  }

  /**
   * Create an assistant agent from a dictionary/object.
   *
   * This method processes the agent specification including tools, and creates
   * or retrieves an assistant from the OpenAI API.
   *
   * @param options - Configuration options
   * @param options.data - The agent specification data
   * @param options.client - OpenAI client instance
   * @param options.kernel - Optional Kernel instance for tool resolution
   * @returns A new OpenAIAssistantAgent instance
   */
  static async fromDict(options: {
    data: Record<string, any>
    client: OpenAI
    kernel?: Kernel
  }): Promise<OpenAIAssistantAgent> {
    const spec = options.data as AgentSpec

    if (!options.client) {
      throw new AgentInitializationException("Missing required 'client' in OpenAIAssistantAgent.fromDict()")
    }

    const kernel = options.kernel
    let definition: Assistant

    if (spec.id) {
      // Retrieve existing assistant
      const existingDefinition = await options.client.beta.assistants.retrieve(spec.id)

      // Create a mutable clone by spreading properties
      definition = { ...existingDefinition }

      // Selectively override attributes from spec
      if (spec.name !== undefined) {
        definition.name = spec.name
      }
      if (spec.description !== undefined) {
        definition.description = spec.description
      }
      if (spec.instructions !== undefined) {
        definition.instructions = spec.instructions
      }
      if (spec.extras) {
        // Merge metadata
        const existingMetadata = definition.metadata || {}
        definition.metadata = { ...existingMetadata, ...spec.extras }
      }

      return new OpenAIAssistantAgent({
        client: options.client,
        definition,
        kernel,
      })
    }

    // Create new assistant
    if (!spec.model?.id) {
      throw new AgentInitializationException('model.id required when creating a new OpenAI assistant')
    }

    // Build tool definitions and resources from spec
    const toolObjs: Array<[AssistantTool[], AssistantCreateParams.ToolResources]> = []

    if (spec.tools && spec.tools.length > 0) {
      // Filter out function tools (handled separately) and build other tools
      const nonFunctionTools = spec.tools.filter((t) => t.type !== 'function')

      for (const toolSpec of nonFunctionTools) {
        try {
          const toolResult = buildTool(toolSpec, kernel)
          toolObjs.push(toolResult)
        } catch (error) {
          throw new AgentInitializationException(
            `Failed to build tool of type '${toolSpec.type}': ${error instanceof Error ? error.message : String(error)}`
          )
        }
      }
    }

    // Merge all tools and resources
    const allTools: AssistantTool[] = []
    const allResources: AssistantCreateParams.ToolResources = {}

    for (const [tools, resources] of toolObjs) {
      allTools.push(...tools)
      Object.assign(allResources, resources)
    }

    // Create the assistant with merged tools and resources
    try {
      definition = await options.client.beta.assistants.create({
        model: spec.model.id,
        name: spec.name,
        description: spec.description,
        instructions: spec.instructions,
        tools: allTools.length > 0 ? allTools : undefined,
        tool_resources: Object.keys(allResources).length > 0 ? allResources : undefined,
        metadata: spec.extras,
      })
    } catch (error) {
      throw new AgentInitializationException(
        `Failed to create OpenAI assistant: ${error instanceof Error ? error.message : String(error)}`
      )
    }

    return new OpenAIAssistantAgent({
      client: options.client,
      definition,
      kernel,
    })
  }
}
