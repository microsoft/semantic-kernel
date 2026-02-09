import { ChatMessageContent } from '../../contents/chat-message-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { AuthorRole } from '../../contents/utils/author-role'
import { Kernel } from '../../kernel'
import { Agent, AgentResponseItem, AgentSpec, AgentThread, IntermediateMessageCallback, ToolSpec } from '../agent'

/**
 * Tool builder function type.
 * Takes a tool spec and optional kernel, returns tools array and resources object.
 */
type ToolBuilder = (spec: ToolSpec, kernel?: Kernel) => [any[], any]

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
function buildTool(spec: ToolSpec, kernel?: Kernel): [any[], any] {
  if (!spec.type) {
    throw new Error('Tool spec must include a "type" field.')
  }

  const builder = TOOL_BUILDERS.get(spec.type.toLowerCase())
  if (!builder) {
    throw new Error(`Unsupported tool type: ${spec.type}`)
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
    throw new Error(`Missing or malformed 'vector_store_ids' in tool spec: ${JSON.stringify(spec)}`)
  }
  return OpenAIAssistantAgent.configureFileSearchTool({ vectorStoreIds })
})

/**
 * OpenAI Assistant Agent Thread class.
 *
 * Note: This class is marked as 'release_candidate' and may change in the future.
 */
export class AssistantAgentThread extends AgentThread {
  protected _client: any // AsyncOpenAI client type
  protected _messages?: any[]
  protected _metadata?: Record<string, any>
  protected _toolResources?: any

  constructor(options: {
    client: any
    threadId?: string
    messages?: any[]
    metadata?: Record<string, any>
    toolResources?: any
  }) {
    super()

    if (!options.client) {
      throw new Error('Client cannot be null')
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
      throw new Error('The thread could not be created due to an error response from the service.', {
        cause: error,
      })
    }
  }

  /**
   * Ends the current thread.
   */
  protected async _delete(): Promise<void> {
    if (!this._id) {
      throw new Error('The thread cannot be deleted because it has not been created yet.')
    }
    try {
      await this._client.beta.threads.delete(this._id)
    } catch (error) {
      throw new Error('The thread could not be deleted due to an error response from the service.', {
        cause: error,
      })
    }
  }

  /**
   * Called when a new message has been contributed to the chat.
   */
  protected async _onNewMessage(newMessage: string | ChatMessageContent): Promise<void> {
    let message: ChatMessageContent
    if (typeof newMessage === 'string') {
      message = new ChatMessageContent({
        role: AuthorRole.USER,
        content: newMessage,
      })
    } else {
      message = newMessage
    }

    // Only add the message to the thread if it's not already there
    if (!message.metadata || !message.metadata.thread_id || message.metadata.thread_id !== this._id) {
      if (!this._id) {
        throw new Error('Thread ID is not set')
      }
      // Add message to thread via OpenAI API
      await this._client.beta.threads.messages.create(this._id, {
        role: message.role,
        content: message.content,
      })
    }
  }

  /**
   * Get the messages in the thread.
   */
  async *getMessages(sortOrder?: 'asc' | 'desc'): AsyncIterable<ChatMessageContent> {
    if (this._isDeleted) {
      throw new Error('The thread has been deleted.')
    }
    if (!this._id) {
      await this.create()
    }
    if (!this._id) {
      throw new Error('Thread ID is not available')
    }

    const messages = await this._client.beta.threads.messages.list(this._id, {
      order: sortOrder,
    })

    for (const message of messages.data) {
      yield new ChatMessageContent({
        role: message.role as AuthorRole,
        content: message.content.map((c: any) => c.text?.value || '').join(''),
        metadata: { thread_id: this._id, message_id: message.id },
      })
    }
  }
}

/**
 * Polling options for OpenAI Assistant runs.
 */
export interface RunPollingOptions {
  /**
   * Maximum time to wait for a run to complete (in milliseconds).
   */
  maxPollingTime?: number

  /**
   * Interval between polling checks (in milliseconds).
   */
  pollingInterval?: number
}

/**
 * OpenAI Assistant Agent class.
 *
 * Provides the ability to interact with OpenAI Assistants.
 *
 * Note: This class is marked as 'release_candidate' and may change in the future.
 */
export class OpenAIAssistantAgent extends Agent {
  client: any // AsyncOpenAI client type
  definition: any // OpenAI Assistant definition
  plugins: any[] = []
  pollingOptions: RunPollingOptions = {
    maxPollingTime: 300000, // 5 minutes
    pollingInterval: 1000, // 1 second
  }

  constructor(options: {
    client: any
    definition: any
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
   * Create an OpenAI client.
   *
   * Note: This method requires the OpenAI SDK to be installed and imported.
   * Import OpenAI from 'openai' package: `import OpenAI from 'openai'`
   *
   * @param options - Configuration options for the OpenAI client
   * @param options.apiKey - The OpenAI API key (can also be set via OPENAI_API_KEY env var)
   * @param options.orgId - The OpenAI organization ID (optional)
   * @param options.defaultHeaders - Additional headers to include in requests (optional)
   * @returns An OpenAI client instance
   * @throws Error if API key is not provided
   *
   * @example
   * ```typescript
   * import OpenAI from 'openai'
   *
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
  }): any {
    // Get API key from options or environment variable
    const apiKey = options.apiKey || process.env.OPENAI_API_KEY

    if (!apiKey) {
      throw new Error(
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

    // Note: This creates a plain object that matches the OpenAI client interface
    // In actual usage, you would import OpenAI from 'openai' package and use:
    // return new OpenAI({
    //   apiKey,
    //   organization: options.orgId,
    //   defaultHeaders: mergedHeaders,
    //   baseURL: options.baseURL
    // })

    // For now, we return a configuration object that can be used to create an OpenAI client
    return {
      apiKey,
      organization: options.orgId,
      defaultHeaders: mergedHeaders,
      baseURL: options.baseURL,
      _note: 'To use this with the OpenAI SDK, import OpenAI and pass these options to the constructor',
    }
  }

  /**
   * Configure code interpreter tool.
   */
  static configureCodeInterpreterTool(options?: { fileIds?: string[] }): [any[], any] {
    const tools = [{ type: 'code_interpreter' }]
    const resources: any = {}

    if (options?.fileIds && options.fileIds.length > 0) {
      resources.code_interpreter = { file_ids: options.fileIds }
    }

    return [tools, resources]
  }

  /**
   * Configure file search tool.
   */
  static configureFileSearchTool(options: { vectorStoreIds: string[] }): [any[], any] {
    if (!options.vectorStoreIds || options.vectorStoreIds.length === 0) {
      throw new Error('vectorStoreIds is required for file search tool')
    }

    const tools = [{ type: 'file_search' }]
    const resources = {
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
        throw new Error('jsonSchema is required when type is "json_schema"')
      }

      if (!options.jsonSchema.name) {
        throw new Error('jsonSchema.name is required')
      }

      if (!options.jsonSchema.schema) {
        throw new Error('jsonSchema.schema is required')
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

    throw new Error(`Unsupported response format type: ${options.type}`)
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
   *   console.log('Channel key:', key)
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
   * Private helper method to run the assistant and yield response items.
   *
   * @private
   */
  private async *_runAssistant(options: {
    thread: AssistantAgentThread
    instructions?: string
    onIntermediateMessage?: IntermediateMessageCallback
  }): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
    // Create run
    const run = await this.client.beta.threads.runs.create(options.thread.id!, {
      assistant_id: this.definition.id,
      instructions: options.instructions || this.instructions,
    })

    // Poll run until completion
    let currentRun = run
    const processedStepIds = new Set<string>()

    while (currentRun.status !== 'completed') {
      // Wait before polling
      await new Promise((resolve) => setTimeout(resolve, this.pollingOptions.pollingInterval))

      // Get updated run status
      currentRun = await this.client.beta.threads.runs.retrieve(options.thread.id!, currentRun.id)

      // Handle error states
      if (['failed', 'cancelled', 'expired', 'incomplete'].includes(currentRun.status)) {
        const errorMsg = currentRun.last_error?.message || `Run failed with status: ${currentRun.status}`
        throw new Error(`Assistant run failed: ${errorMsg}`)
      }

      // Handle function calls (requires_action)
      if (currentRun.status === 'requires_action') {
        const toolCalls = currentRun.required_action?.submit_tool_outputs?.tool_calls
        if (toolCalls && toolCalls.length > 0) {
          const toolOutputs: any[] = []

          for (const toolCall of toolCalls) {
            if (toolCall.type === 'function') {
              const functionName = toolCall.function.name
              const functionArgs = JSON.parse(toolCall.function.arguments)

              // Execute the function through the kernel
              try {
                const result = await this.kernel.invoke({
                  pluginName: '',
                  functionName,
                  arguments: functionArgs,
                })
                toolOutputs.push({
                  tool_call_id: toolCall.id,
                  output: JSON.stringify(result),
                })

                // Emit intermediate message if callback is provided
                if (options.onIntermediateMessage) {
                  const intermediateMsg = new ChatMessageContent({
                    role: AuthorRole.TOOL,
                    content: `Function ${functionName} called with result: ${JSON.stringify(result)}`,
                    metadata: { function_name: functionName, function_args: functionArgs },
                  })
                  await options.onIntermediateMessage(intermediateMsg)
                }
              } catch (error) {
                toolOutputs.push({
                  tool_call_id: toolCall.id,
                  output: JSON.stringify({ error: String(error) }),
                })
              }
            }
          }

          // Submit tool outputs
          await this.client.beta.threads.runs.submitToolOutputs(options.thread.id!, currentRun.id, {
            tool_outputs: toolOutputs,
          })
        }
        continue
      }

      // Get completed steps
      const stepsResponse = await this.client.beta.threads.runs.steps.list(options.thread.id!, currentRun.id)
      const steps = stepsResponse.data

      const completedSteps = steps.filter((step: any) => step.completed_at !== null && !processedStepIds.has(step.id))

      // Process completed steps
      for (const step of completedSteps) {
        processedStepIds.add(step.id)

        if (step.type === 'message_creation') {
          // Retrieve the message
          const messageId = step.step_details?.message_creation?.message_id
          if (messageId) {
            const message = await this.client.beta.threads.messages.retrieve(options.thread.id!, messageId)

            // Extract text content
            const textContent = message.content
              .filter((c: any) => c.type === 'text')
              .map((c: any) => c.text.value)
              .join('\n')

            if (textContent) {
              const chatMessage = new ChatMessageContent({
                role: AuthorRole.ASSISTANT,
                content: textContent,
                metadata: {
                  thread_id: options.thread.id,
                  message_id: messageId,
                  run_id: currentRun.id,
                },
              })

              yield new AgentResponseItem(chatMessage, options.thread)
            }
          }
        } else if (step.type === 'tool_calls') {
          // Handle tool call steps (code interpreter, etc.)
          const toolCalls = step.step_details?.tool_calls
          if (toolCalls && options.onIntermediateMessage) {
            for (const toolCall of toolCalls) {
              if (toolCall.type === 'code_interpreter') {
                const intermediateMsg = new ChatMessageContent({
                  role: AuthorRole.TOOL,
                  content: `Code interpreter executed: ${toolCall.code_interpreter?.input || ''}`,
                  metadata: { type: 'code_interpreter', step_id: step.id },
                })
                await options.onIntermediateMessage(intermediateMsg)
              }
            }
          }
        }
      }
    }
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
    [key: string]: any
  }): Promise<AgentResponseItem<ChatMessageContent>> {
    // Prepare thread and add messages
    const assistantThread = await this._prepareThread(options)

    // Format instructions
    const instructions = options.instructionsOverride || (await this.formatInstructions(this.kernel, this.arguments))

    // Collect all response messages
    const responseMessages: ChatMessageContent[] = []
    for await (const responseItem of this._runAssistant({
      thread: assistantThread,
      instructions,
    })) {
      responseMessages.push(responseItem.message)
    }

    // Return the final message
    if (responseMessages.length === 0) {
      throw new Error('No response messages were returned from the agent.')
    }

    const finalMessage = responseMessages[responseMessages.length - 1]
    await assistantThread.onNewMessage(finalMessage)

    return new AgentResponseItem(finalMessage, assistantThread)
  }

  /**
   * Invoke the assistant and get responses.
   */
  async *invoke(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    onIntermediateMessage?: IntermediateMessageCallback
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
    // Prepare thread and add messages
    const assistantThread = await this._prepareThread(options)

    // Format instructions
    const instructions = await this.formatInstructions(this.kernel, this.arguments)

    // Yield response items as they arrive
    yield* this._runAssistant({
      thread: assistantThread,
      instructions,
      onIntermediateMessage: options.onIntermediateMessage,
    })
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
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
    // Prepare thread and add messages
    const assistantThread = await this._prepareThread(options)

    // Format instructions
    const instructions = await this.formatInstructions(this.kernel, this.arguments)

    // Create streaming run
    const stream = await this.client.beta.threads.runs.stream(assistantThread.id!, {
      assistant_id: this.definition.id,
      instructions: instructions || this.instructions,
    })

    // Track active messages and function steps
    const collectedMessages: ChatMessageContent[] = []
    let startIdx = 0

    // Process streaming events
    for await (const event of stream) {
      // Handle different event types
      if (event.event === 'thread.run.created') {
        // Run created, nothing to yield yet
        continue
      } else if (event.event === 'thread.run.in_progress') {
        // Run in progress, nothing to yield yet
        continue
      } else if (event.event === 'thread.message.delta') {
        // Streaming message content delta
        const delta = event.data.delta
        if (delta?.content) {
          for (const contentPart of delta.content) {
            if (contentPart.type === 'text' && contentPart.text?.value) {
              const streamingMessage = new StreamingChatMessageContent({
                role: AuthorRole.ASSISTANT,
                choiceIndex: 0,
                content: contentPart.text.value,
                metadata: {
                  thread_id: assistantThread.id,
                  message_id: event.data.id,
                },
              })

              yield new AgentResponseItem(streamingMessage, assistantThread)
            }
          }
        }
      } else if (event.event === 'thread.run.step.completed') {
        // Step completed - collect full messages for intermediate callback
        const step = event.data
        if (step.type === 'message_creation') {
          const messageId = step.step_details?.message_creation?.message_id
          if (messageId) {
            const message = await this.client.beta.threads.messages.retrieve(assistantThread.id!, messageId)
            const textContent = message.content
              .filter((c: any) => c.type === 'text')
              .map((c: any) => c.text.value)
              .join('\n')

            if (textContent) {
              const chatMessage = new ChatMessageContent({
                role: AuthorRole.ASSISTANT,
                content: textContent,
                metadata: {
                  thread_id: assistantThread.id,
                  message_id: messageId,
                },
              })
              collectedMessages.push(chatMessage)
            }
          }
        }
      } else if (event.event === 'thread.run.step.delta') {
        // Step delta - handle tool calls
        const stepDetails = event.data.delta?.step_details
        if (stepDetails?.type === 'tool_calls' && stepDetails.tool_calls) {
          for (const toolCall of stepDetails.tool_calls) {
            if (toolCall.type === 'code_interpreter' && toolCall.code_interpreter?.input) {
              const streamingMessage = new StreamingChatMessageContent({
                role: AuthorRole.TOOL,
                choiceIndex: 0,
                content: toolCall.code_interpreter.input,
                metadata: {
                  type: 'code_interpreter',
                  thread_id: assistantThread.id,
                },
              })

              yield new AgentResponseItem(streamingMessage, assistantThread)
            }
          }
        }
      } else if (event.event === 'thread.run.requires_action') {
        // Handle function calls
        const run = event.data
        const toolCalls = run.required_action?.submit_tool_outputs?.tool_calls
        if (toolCalls && toolCalls.length > 0) {
          const toolOutputs: any[] = []

          for (const toolCall of toolCalls) {
            if (toolCall.type === 'function') {
              const functionName = toolCall.function.name
              const functionArgs = JSON.parse(toolCall.function.arguments)

              // Execute the function through the kernel
              try {
                const result = await this.kernel.invoke({
                  pluginName: '',
                  functionName,
                  arguments: functionArgs,
                })
                toolOutputs.push({
                  tool_call_id: toolCall.id,
                  output: JSON.stringify(result),
                })

                // Emit intermediate message if callback is provided
                if (options.onIntermediateMessage) {
                  const intermediateMsg = new ChatMessageContent({
                    role: AuthorRole.TOOL,
                    content: `Function ${functionName} called with result: ${JSON.stringify(result)}`,
                    metadata: { function_name: functionName, function_args: functionArgs },
                  })
                  await options.onIntermediateMessage(intermediateMsg)
                }
              } catch (error) {
                toolOutputs.push({
                  tool_call_id: toolCall.id,
                  output: JSON.stringify({ error: String(error) }),
                })
              }
            }
          }

          // Submit tool outputs and continue streaming
          await this.client.beta.threads.runs.submitToolOutputs(assistantThread.id!, run.id, {
            tool_outputs: toolOutputs,
          })
        }
      } else if (event.event === 'thread.run.completed') {
        // Run completed - emit any new intermediate messages
        if (options.onIntermediateMessage) {
          const newMessages = collectedMessages.slice(startIdx)
          for (const msg of newMessages) {
            await assistantThread.onNewMessage(msg)
            await options.onIntermediateMessage(msg)
          }
        }
        break
      } else if (
        event.event === 'thread.run.failed' ||
        event.event === 'thread.run.cancelled' ||
        event.event === 'thread.run.expired'
      ) {
        const errorMsg = event.data.last_error?.message || `Run ended with status: ${event.event}`
        throw new Error(`Assistant run failed: ${errorMsg}`)
      }

      // Before yielding, emit any new collected messages via callback
      if (options.onIntermediateMessage) {
        const newMessages = collectedMessages.slice(startIdx)
        startIdx = collectedMessages.length
        for (const msg of newMessages) {
          await assistantThread.onNewMessage(msg)
          await options.onIntermediateMessage(msg)
        }
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
    client: any
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
      throw new Error(
        'fromYaml requires YAML content to be parsed. Please install a YAML parsing library ' +
          '(e.g., "yaml" or "js-yaml") and parse the YAML before calling fromDict, or provide JSON format. ' +
          `Parse error: ${jsonError}`,
        { cause: jsonError }
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
    client: any
    kernel?: Kernel
  }): Promise<OpenAIAssistantAgent> {
    const spec = options.data as AgentSpec

    if (!options.client) {
      throw new Error("Missing required 'client' in OpenAIAssistantAgent.fromDict()")
    }

    const kernel = options.kernel
    let definition: any

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
      throw new Error('model.id required when creating a new OpenAI assistant')
    }

    // Build tool definitions and resources from spec
    const toolObjs: Array<[any[], any]> = []

    if (spec.tools && spec.tools.length > 0) {
      // Filter out function tools (handled separately) and build other tools
      const nonFunctionTools = spec.tools.filter((t) => t.type !== 'function')

      for (const toolSpec of nonFunctionTools) {
        try {
          const toolResult = buildTool(toolSpec, kernel)
          toolObjs.push(toolResult)
        } catch (error) {
          throw new Error(
            `Failed to build tool of type '${toolSpec.type}': ${error instanceof Error ? error.message : String(error)}`,
            { cause: error }
          )
        }
      }
    }

    // Merge all tools and resources
    const allTools: any[] = []
    const allResources: Record<string, any> = {}

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
      throw new Error(`Failed to create OpenAI assistant: ${error instanceof Error ? error.message : String(error)}`, {
        cause: error,
      })
    }

    return new OpenAIAssistantAgent({
      client: options.client,
      definition,
      kernel,
    })
  }
}
