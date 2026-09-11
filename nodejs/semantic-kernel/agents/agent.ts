import { randomUUID } from 'crypto'
import { ChatMessageContent, CMCItemTypes } from '../contents/chat-message-content'
import { StreamingChatMessageContent } from '../contents/streaming-chat-message-content'
import { AuthorRole } from '../contents/utils/author-role'
import {
  AgentExecutionException,
  AgentInitializationException,
  AgentThreadOperationException,
} from '../exceptions/agent-exceptions'
import { KernelArguments } from '../functions/kernel-arguments'
import { Kernel, KernelPlugin, PromptExecutionSettings, PromptTemplateConfig } from '../kernel'
import { createDefaultLogger, Logger } from '../utils/logger'

// #region Declarative Spec Definitions

/**
 * Class representing an input specification.
 */
export interface InputSpec {
  description?: string
  required?: boolean
  default?: any
}

/**
 * Class representing an output specification.
 */
export interface OutputSpec {
  description?: string
  type?: string
}

/**
 * Class representing a model connection.
 */
export interface ModelConnection {
  type?: string
  serviceId?: string
  extras?: Record<string, any>
}

/**
 * Class representing a model specification.
 */
export interface ModelSpec {
  id?: string
  api?: string
  options?: Record<string, any>
  connection?: ModelConnection
}

/**
 * Class representing a tool specification.
 */
export interface ToolSpec {
  id?: string
  type?: string
  description?: string
  options?: Record<string, any>
  extras?: Record<string, any>
}

/**
 * Class representing an agent specification.
 */
export interface AgentSpec {
  type: string
  id?: string
  name?: string
  description?: string
  instructions?: string
  model?: ModelSpec
  tools?: ToolSpec[]
  template?: Record<string, any>
  extras?: Record<string, any>
  inputs?: Record<string, InputSpec>
  outputs?: Record<string, OutputSpec>
}

// #endregion

// Create module-level logger
const logger: Logger = createDefaultLogger('Agent')

// #region AgentThread

/**
 * Base class for agent threads.
 */
export abstract class AgentThread {
  protected _isDeleted: boolean = false
  protected _id?: string

  /**
   * Returns the ID of the current thread (if any).
   */
  get id(): string | undefined {
    if (this._isDeleted) {
      logger.error("Thread has been deleted; call 'create()' to recreate it.")
      throw new AgentThreadOperationException("Thread has been deleted; call 'create()' to recreate it.")
    }
    return this._id
  }

  /**
   * Starts the thread and returns the thread ID.
   */
  async create(): Promise<string | undefined> {
    // A thread should not be recreated after it has been deleted.
    if (this._isDeleted) {
      logger.error('Cannot create thread because it has already been deleted.')
      throw new AgentThreadOperationException('Cannot create thread because it has already been deleted.')
    }

    // If the thread ID is already set, we're done, just return the Id.
    if (this.id !== undefined) {
      logger.debug(`Thread already created with ID: ${this.id}`)
      return this.id
    }

    // Otherwise, create the thread.
    this._id = await this._create()
    logger.info(`Thread created with ID: ${this._id}`)
    return this.id
  }

  /**
   * Ends the current thread.
   */
  async delete(): Promise<void> {
    // A thread should not be deleted if it has already been deleted.
    if (this._isDeleted) {
      logger.debug('Thread already deleted, skipping.')
      return
    }

    // If the thread ID is not set, we're done, just return.
    if (this.id === undefined) {
      this._isDeleted = true
      logger.debug('Thread was not created, marking as deleted.')
      return
    }

    // Otherwise, delete the thread.
    logger.info(`Deleting thread with ID: ${this.id}`)
    await this._delete()
    this._id = undefined
    this._isDeleted = true
  }

  /**
   * Invoked when a new message has been contributed to the chat by any participant.
   */
  async onNewMessage(newMessage: ChatMessageContent): Promise<void> {
    // If the thread is not created yet, create it.
    if (this.id === undefined) {
      logger.debug('Thread not created yet, creating now.')
      await this.create()
    }

    logger.debug(`Processing new message in thread ${this.id}`)
    await this._onNewMessage(newMessage)
  }

  /**
   * Starts the thread and returns the thread ID.
   */
  protected abstract _create(): Promise<string>

  /**
   * Ends the current thread.
   */
  protected abstract _delete(): Promise<void>

  /**
   * Invoked when a new message has been contributed to the chat by any participant.
   */
  protected abstract _onNewMessage(newMessage: ChatMessageContent): Promise<void>
}

// #endregion

// #region AgentResponseItem

/**
 * Class representing a response item from an agent.
 */
export class AgentResponseItem<TMessage extends ChatMessageContent> {
  message: TMessage
  thread: AgentThread

  constructor(message: TMessage, thread: AgentThread) {
    this.message = message
    this.thread = thread
  }

  /**
   * Get the content of the response item.
   */
  get content(): TMessage {
    return this.message
  }

  /**
   * Get the items of the response item.
   */
  get items(): CMCItemTypes[] {
    return this.message.items
  }

  /**
   * Get the metadata of the response item.
   */
  get metadata(): Record<string, any> {
    return this.message.metadata
  }

  /**
   * Get the name of the response item.
   */
  get name(): string | undefined {
    return this.message.name
  }

  /**
   * Get the role of the response item.
   */
  get role(): string | AuthorRole | undefined {
    return this.message.role
  }

  /**
   * Get the string representation of the response item.
   */
  toString(): string {
    return this.content.toString()
  }

  /**
   * Get the hash of the response item.
   */
  hash(): number {
    // Simple hash implementation combining message and thread
    let hash = 0
    const str = `${this.message.content}${this.thread.id || ''}`
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = (hash << 5) - hash + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return hash
  }
}

// #endregion

// #region Agent Base Class

/**
 * Configuration options for creating an agent.
 */
export interface AgentConfig {
  id?: string
  name?: string
  description?: string
  instructions?: string
  kernel?: Kernel
  plugins?: KernelPlugin[]
  arguments?: KernelArguments
  promptTemplate?: PromptTemplateBase
}

/**
 * Base interface for prompt templates.
 */
export interface PromptTemplateBase {
  render(kernel: Kernel, arguments_?: KernelArguments): Promise<string>
}

/**
 * Callback type for handling intermediate messages.
 */
export type IntermediateMessageCallback = (message: ChatMessageContent) => Promise<void>

/**
 * Base abstraction for all Semantic Kernel agents.
 *
 * An agent instance may participate in one or more conversations.
 * A conversation may include one or more agents.
 * In addition to identity and descriptive meta-data, an Agent
 * must define its communication protocol, or AgentChannel.
 */
export abstract class Agent {
  readonly id: string
  name: string
  description?: string
  instructions?: string
  kernel: Kernel
  arguments?: KernelArguments
  promptTemplate?: PromptTemplateBase

  protected static channelType?: new () => AgentChannel

  /**
   * Helper method to get the plugin name.
   */
  protected static _getPluginName(plugin: KernelPlugin | object): string {
    if ('name' in plugin && typeof plugin.name === 'string') {
      return plugin.name
    }
    return plugin.constructor.name
  }

  constructor(config: AgentConfig = {}) {
    this.id = config.id || randomUUID()
    this.name = config.name || `agent_${this._generateRandomName()}`
    this.description = config.description
    this.instructions = config.instructions
    this.kernel = config.kernel || new Kernel()
    this.arguments = config.arguments
    this.promptTemplate = config.promptTemplate

    logger.debug(`Creating agent: ${this.name} (ID: ${this.id})`)

    // Configure plugins if provided
    if (config.plugins) {
      logger.debug(`Configuring ${config.plugins.length} plugin(s) for agent ${this.name}`)
      for (const plugin of config.plugins) {
        this.kernel.addPlugin(plugin)
      }
    }

    this._postInit()
    logger.info(`Agent created: ${this.name} (ID: ${this.id})`)
  }

  /**
   * Post initialization: create a kernel function that calls this agent's getResponse().
   */
  protected _postInit(): void {
    // Create a minimal universal function for all agents
    const asKernelFunction = async (messages: string | string[], instructionsOverride?: string): Promise<any> => {
      const messageArray = Array.isArray(messages) ? messages : [messages]

      logger.debug(`Calling agent ${this.name} as kernel function with ${messageArray.length} message(s)`)

      const responseItem = await this.getResponse({
        messages: messageArray,
        instructionsOverride: instructionsOverride || undefined,
      })
      return responseItem.content
    }

    // Store the function for potential use
    ;(this as any)._asKernelFunction = asKernelFunction
  }

  /**
   * Generate a random ASCII name.
   */
  protected _generateRandomName(): string {
    const chars = 'abcdefghijklmnopqrstuvwxyz'
    let result = ''
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  // #region Invocation Methods

  /**
   * Get a response from the agent.
   *
   * This method returns the final result of the agent's execution
   * as a single ChatMessageContent object. The caller is blocked until
   * the final result is available.
   *
   * Note: For streaming responses, use the invokeStream method, which returns
   * intermediate steps and the final result as a stream of StreamingChatMessageContent
   * objects. Streaming only the final result is not feasible because the timing of
   * the final result's availability is unknown, and blocking the caller until then
   * is undesirable in streaming scenarios.
   */
  abstract getResponse(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    instructionsOverride?: string
    [key: string]: any
  }): Promise<AgentResponseItem<ChatMessageContent>>

  /**
   * Invoke the agent.
   *
   * This invocation method will return the final results of the agent's execution as a
   * stream of ChatMessageContent objects to the caller. The reason for returning a stream
   * is to allow for future extensions to the agent's capabilities, such as multi-modality.
   *
   * To get the intermediate steps of the agent's execution, use the onIntermediateMessage callback
   * to handle those messages.
   *
   * Note: A ChatMessageContent object contains an entire message.
   */
  abstract invoke(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    onIntermediateMessage?: IntermediateMessageCallback
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<ChatMessageContent>>

  /**
   * Invoke the agent as a stream.
   *
   * This invocation method will return the intermediate steps and final results of the
   * agent's execution as a stream of StreamingChatMessageContent objects to the caller.
   *
   * To get the intermediate steps of the agent's execution as fully formed messages,
   * use the onIntermediateMessage callback.
   *
   * Note: A StreamingChatMessageContent object contains a chunk of a message.
   */
  abstract invokeStream(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    onIntermediateMessage?: IntermediateMessageCallback
    [key: string]: any
  }): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>>

  // #endregion

  // #region Channel Management

  /**
   * Get the channel keys.
   */
  *getChannelKeys(): Iterable<string> {
    const channelType = (this.constructor as typeof Agent).channelType
    if (!channelType) {
      logger.error('Unable to get channel keys. Channel type not configured.')
      throw new AgentInitializationException('Unable to get channel keys. Channel type not configured.')
    }
    yield channelType.name
  }

  /**
   * Create a channel.
   */
  async createChannel(): Promise<AgentChannel> {
    const channelType = (this.constructor as typeof Agent).channelType
    if (!channelType) {
      logger.error('Unable to create channel. Channel type not configured.')
      throw new AgentInitializationException('Unable to create channel. Channel type not configured.')
    }
    logger.debug(`Creating channel of type: ${channelType.name}`)
    return new channelType()
  }

  // #endregion

  // #region Instructions Management

  /**
   * Format the instructions.
   */
  async formatInstructions(kernel: Kernel, arguments_?: KernelArguments): Promise<string | undefined> {
    if (this.promptTemplate === undefined) {
      if (this.instructions === undefined) {
        logger.debug(`Agent ${this.name} has no instructions to format`)
        return undefined
      }
      // Create a basic prompt template if instructions are set
      logger.debug(`Creating default prompt template for agent ${this.name}`)
      this.promptTemplate = new KernelPromptTemplate({ template: this.instructions })
    }
    logger.debug(`Formatting instructions for agent ${this.name}`)
    return await this.promptTemplate.render(kernel, arguments_)
  }

  /**
   * Merge the arguments with the override arguments.
   */
  protected _mergeArguments(overrideArgs?: KernelArguments): KernelArguments {
    if (!this.arguments) {
      if (!overrideArgs) {
        return new KernelArguments()
      }

      return overrideArgs
    }

    if (!overrideArgs) {
      return this.arguments
    }

    // Both are not undefined, so merge with precedence for overrideArgs
    logger.debug(`Merging arguments for agent ${this.name}`)
    return this.arguments.merge(overrideArgs)
  }

  // #endregion

  // #region Thread Management

  /**
   * Ensure the thread exists with the provided message(s).
   */
  protected async _ensureThreadExistsWithMessages<TThreadType extends AgentThread>(options: {
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
    thread?: AgentThread
    constructThread: () => TThreadType
    expectedType: new () => TThreadType
  }): Promise<TThreadType> {
    let { messages, thread } = options
    const { constructThread, expectedType } = options

    if (messages === undefined) {
      messages = []
    }

    if (typeof messages === 'string' || messages instanceof ChatMessageContent) {
      messages = [messages]
    }

    const normalizedMessages = messages.map((msg) =>
      typeof msg === 'string' ? new ChatMessageContent({ role: AuthorRole.USER, content: msg }) : msg
    )

    if (thread === undefined) {
      logger.debug(`Creating new thread for agent ${this.name}`)
      thread = constructThread()
      await thread.create()
    }

    if (!(thread instanceof expectedType)) {
      const errorMsg = `${this.constructor.name} currently only supports agent threads of type ${expectedType.name}.`
      logger.error(errorMsg)
      throw new AgentExecutionException(errorMsg)
    }

    // Track the agent ID as user msg metadata, which is useful for
    // fetching thread messages as the agent may have been deleted.
    const idMetadata = {
      agent_id: this.id,
    }

    // Notify the thread that new messages are available.
    logger.debug(`Notifying thread of ${normalizedMessages.length} new message(s) for agent ${this.name}`)
    for (const msg of normalizedMessages) {
      Object.assign(msg.metadata, idMetadata)
      await this._notifyThreadOfNewMessage(thread, msg)
    }

    return thread as TThreadType
  }

  /**
   * Notify the thread of a new message.
   */
  protected async _notifyThreadOfNewMessage(thread: AgentThread, newMessage: ChatMessageContent): Promise<void> {
    logger.debug(`Notifying thread ${thread.id} of new message`)
    await thread.onNewMessage(newMessage)
  }

  // #endregion

  /**
   * Check if two agents are equal.
   */
  equals(other: any): boolean {
    if (other instanceof Agent) {
      return (
        this.id === other.id &&
        this.name === other.name &&
        this.description === other.description &&
        this.instructions === other.instructions
      )
    }
    return false
  }

  /**
   * Get the hash of the agent.
   */
  hash(): number {
    // Simple hash implementation
    let hash = 0
    const channelTypeName = (this.constructor as typeof Agent).channelType?.name || ''
    const str = `${this.id}${this.name}${this.description || ''}${this.instructions || ''}${channelTypeName}`
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = (hash << 5) - hash + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return hash
  }

  /**
   * Convert the agent to an MCP server.
   *
   * This will create a MCP Server, with a single Tool, which is the agent itself.
   * Prompts can be added through the prompts parameter.
   *
   * By default, the server name will be the same as the agent name.
   * If a server name is provided, it will be used instead.
   *
   * Note: This is a stub implementation. Full MCP server integration requires
   * the MCP connector module.
   */
  asMcpServer(_options?: {
    prompts?: PromptTemplateBase[]
    serverName?: string
    version?: string
    instructions?: string
    lifespan?: any
  }): any {
    logger.error('MCP server conversion not yet implemented in TypeScript')
    throw new AgentInitializationException(
      'MCP server conversion not yet implemented in TypeScript. ' +
        'This requires the semantic-kernel.connectors.mcp module to be ported.'
    )
  }
}

// #endregion

// #region AgentChannel

/**
 * Base class for agent channels.
 */
export abstract class AgentChannel {
  // Channel implementation would go here
}

// #endregion

// #region Declarative Spec Handling

/**
 * Agent type registry.
 */
const AGENT_TYPE_REGISTRY: Map<string, new (...args: any[]) => Agent> = new Map()

/**
 * Decorator to register an agent type with the registry.
 *
 * Example usage:
 *   @registerAgentType('my_custom_agent')
 *   class MyCustomAgent extends Agent {
 *     ...
 *   }
 */
export function registerAgentType(agentType: string) {
  return function <T extends new (...args: any[]) => Agent>(constructor: T) {
    logger.debug(`Registering agent type: ${agentType}`)
    AGENT_TYPE_REGISTRY.set(agentType.toLowerCase(), constructor)
    return constructor
  }
}

/**
 * Interface for declarative spec support.
 */
export interface DeclarativeSpecSupport {
  resolvePlaceholders(yamlStr: string, settings?: any, extras?: Record<string, any>): string
  fromYaml(options: {
    yamlStr: string
    kernel?: Kernel
    plugins?: KernelPlugin[]
    settings?: any
    extras?: Record<string, any>
    [key: string]: any
  }): Promise<Agent>
  fromDict(options: {
    data: Record<string, any>
    kernel?: Kernel
    plugins?: KernelPlugin[]
    settings?: any
    [key: string]: any
  }): Promise<Agent>
}

/**
 * Agent registry for creating agents from YAML, dicts, or files.
 */
export class AgentRegistry {
  /**
   * Register a new agent type at runtime.
   */
  static registerType(agentType: string, agentCls: new (...args: any[]) => Agent): void {
    logger.info(`Registering agent type at runtime: ${agentType}`)
    AGENT_TYPE_REGISTRY.set(agentType.toLowerCase(), agentCls)
  }

  /**
   * Create a single agent instance from a YAML string.
   */
  static async createFromYaml(options: {
    yamlStr: string
    kernel?: Kernel
    plugins?: KernelPlugin[]
    settings?: any
    extras?: Record<string, any>
    [key: string]: any
  }): Promise<Agent> {
    let { yamlStr } = options
    const yaml = await import('yaml')

    logger.debug('Parsing agent definition from YAML')

    // First parse to get the agent type
    let data = yaml.parse(yamlStr) as Record<string, any>

    const agentType = (data.type || '').toLowerCase()
    if (!agentType) {
      logger.error("Missing 'type' field in agent definition")
      throw new AgentInitializationException("Missing 'type' field in agent definition.")
    }

    const agentCls = AGENT_TYPE_REGISTRY.get(agentType)
    if (!agentCls) {
      logger.error(`Agent type '${agentType}' not registered`)
      throw new AgentInitializationException(`Agent type '${agentType}' not registered.`)
    }

    // Check if the class supports declarative spec
    if (typeof (agentCls as any).fromDict !== 'function') {
      logger.error(`Agent class '${agentCls.name}' does not support declarative spec loading`)
      throw new AgentInitializationException(
        `Agent class '${agentCls.name}' does not support declarative spec loading.`
      )
    }

    // Resolve placeholders if the class supports it
    if (typeof (agentCls as any).resolvePlaceholders === 'function') {
      logger.debug('Resolving placeholders in YAML')
      yamlStr = (agentCls as any).resolvePlaceholders(yamlStr, options.settings, options.extras)
      data = yaml.parse(yamlStr) as Record<string, any>
    }

    logger.info(`Creating agent of type '${agentType}' from YAML`)
    return await (agentCls as any).fromDict({
      data,
      kernel: options.kernel,
      plugins: options.plugins,
      settings: options.settings,
      ...options,
    })
  }

  /**
   * Create a single agent instance from a dictionary.
   */
  static async createFromDict(options: {
    data: Record<string, any>
    kernel?: Kernel
    plugins?: KernelPlugin[]
    settings?: any
    extras?: Record<string, any>
    [key: string]: any
  }): Promise<Agent> {
    const agentType = (options.data.type || '').toLowerCase()

    if (!agentType) {
      logger.error("Missing 'type' field in agent definition")
      throw new AgentInitializationException("Missing 'type' field in agent definition.")
    }

    const agentCls = AGENT_TYPE_REGISTRY.get(agentType)
    if (!agentCls) {
      logger.error(`Agent type '${agentType}' is not supported`)
      throw new AgentInitializationException(`Agent type '${agentType}' is not supported.`)
    }

    // Check if the class supports declarative spec
    if (typeof (agentCls as any).fromDict !== 'function') {
      logger.error(`Agent class '${agentCls.name}' does not support declarative spec loading`)
      throw new AgentInitializationException(
        `Agent class '${agentCls.name}' does not support declarative spec loading.`
      )
    }

    logger.info(`Creating agent of type '${agentType}' from dictionary`)
    return await (agentCls as any).fromDict(options)
  }

  /**
   * Create a single agent instance from a YAML file.
   */
  static async createFromFile(options: {
    filePath: string
    kernel?: Kernel
    plugins?: KernelPlugin[]
    settings?: any
    extras?: Record<string, any>
    encoding?: string
    [key: string]: any
  }): Promise<Agent> {
    const fs = await import('fs/promises')

    try {
      const encoding = options.encoding || 'utf-8'
      logger.info(`Reading agent spec from file: ${options.filePath}`)
      const yamlStr = await fs.readFile(options.filePath, encoding as BufferEncoding)

      return await AgentRegistry.createFromYaml({
        yamlStr: yamlStr.toString(),
        kernel: options.kernel,
        plugins: options.plugins,
        settings: options.settings,
        extras: options.extras,
        ...options,
      })
    } catch (error) {
      logger.error(`Failed to read agent spec file: ${error}`)
      throw new AgentInitializationException(`Failed to read agent spec file: ${error}`)
    }
  }
}

// #endregion

// #region DeclarativeSpecMixin

/**
 * Mixin class for declarative agent methods.
 */
export abstract class DeclarativeSpecMixin extends Agent {
  /**
   * Create an agent instance from a YAML string.
   */
  static async fromYaml(options: {
    yamlStr: string
    kernel?: Kernel
    plugins?: KernelPlugin[]
    promptTemplateConfig?: PromptTemplateConfig
    settings?: any
    extras?: Record<string, any>
    [key: string]: any
  }): Promise<Agent> {
    let { yamlStr } = options
    const { kernel, plugins, promptTemplateConfig, settings, extras } = options

    logger.debug(`Creating ${this.name} from YAML`)

    if (settings) {
      logger.debug('Resolving placeholders in YAML')
      yamlStr = this.resolvePlaceholders(yamlStr, settings, extras)
    }

    const yaml = await import('yaml')
    const data = yaml.parse(yamlStr)

    return await this.fromDict({
      data,
      kernel,
      plugins,
      promptTemplateConfig,
      settings,
      ...options,
    })
  }

  /**
   * Create an agent instance from a dictionary.
   */
  static async fromDict(options: {
    data: Record<string, any>
    kernel?: Kernel
    plugins?: KernelPlugin[]
    promptTemplateConfig?: PromptTemplateConfig
    settings?: any
    [key: string]: any
  }): Promise<Agent> {
    const { data, plugins } = options
    const { kernel } = options

    logger.debug(`Creating ${this.name} from dictionary`)

    const [extracted, effectiveKernel] = this._normalizeSpecFields({
      kernel,
      plugins,
      ...options,
    })

    return await this._fromDict({
      ...data,
      ...extracted,
      kernel: effectiveKernel,
      promptTemplateConfig: extracted.promptTemplate,
      settings: options.settings,
      ...options,
    })
  }

  /**
   * Create an agent instance from a dictionary (protected method to be implemented by subclasses).
   */
  protected static async _fromDict(_options: {
    data?: Record<string, any>
    kernel: Kernel
    promptTemplateConfig?: PromptTemplateConfig
    [key: string]: any
  }): Promise<Agent> {
    logger.error('_fromDict must be implemented by subclasses')
    throw new AgentInitializationException('_fromDict must be implemented by subclasses')
  }

  /**
   * Resolve placeholders inside the YAML string using agent-specific settings.
   *
   * Override in subclasses if necessary.
   */
  static resolvePlaceholders(yamlStr: string, _settings?: any, _extras?: Record<string, any>): string {
    return yamlStr
  }

  /**
   * Normalize the fields in the spec dictionary.
   */
  protected static _normalizeSpecFields(options: {
    data: Record<string, any>
    kernel?: Kernel
    plugins?: KernelPlugin[]
    [key: string]: any
  }): [Record<string, any>, Kernel] {
    const { data, plugins } = options
    let { kernel } = options

    logger.debug('Normalizing spec fields')

    if (!kernel) {
      logger.debug('No kernel provided, creating new one')
      kernel = new Kernel()
    }

    // Plugins provided explicitly
    if (plugins) {
      logger.debug(`Adding ${plugins.length} plugin(s) to kernel`)
      for (const plugin of plugins) {
        kernel.addPlugin(plugin)
      }
    }

    // Validate tools declared in the spec exist in the kernel
    if (data.tools) {
      logger.debug('Validating tools in spec')
      this._validateTools(data.tools, kernel)
    }

    const modelOptions = data.model?.options || {}
    const inputs = data.inputs || {}
    const inputDefaults: Record<string, any> = {}

    if (typeof inputs === 'object') {
      for (const [k, v] of Object.entries(inputs)) {
        if (typeof v === 'object' && v !== null && 'default' in v && v.default !== undefined) {
          inputDefaults[k] = v.default
        }
      }
    }

    // Convert model options to execution settings
    let arguments_: KernelArguments = new KernelArguments()
    if (Object.keys(modelOptions).length > 0) {
      logger.debug('Converting model options to execution settings')
      const execSettings: PromptExecutionSettings = { ...modelOptions }
      arguments_ = new KernelArguments({ settings: execSettings })
    }

    // Add input defaults as regular items
    for (const [k, v] of Object.entries(inputDefaults)) {
      if (!arguments_.has(k)) {
        arguments_.set(k, v)
      }
    }

    const fields: Record<string, any> = {
      name: data.name,
      description: data.description,
      instructions: data.instructions,
      arguments: arguments_,
    }

    // Handle prompt_template if available (supports both snake_case and camelCase)
    const templateData = data.prompt_template || data.promptTemplate || data.template
    if (templateData) {
      if (typeof templateData === 'object') {
        logger.debug('Processing prompt template configuration')
        const promptTemplateConfig: PromptTemplateConfig = { ...templateData }
        // If 'instructions' is set in YAML, override the template field in config
        if (data.instructions !== undefined) {
          promptTemplateConfig.template = data.instructions
        }
        fields.promptTemplate = promptTemplateConfig
        // Always set fields.instructions to the template being used
        fields.instructions = promptTemplateConfig.template
      }
    }

    return [fields, kernel]
  }

  /**
   * Validate tool references in the declarative spec against kernel's registered plugins.
   */
  protected static _validateTools(toolsList: any[], kernel: Kernel): void {
    if (!kernel) {
      logger.error('Kernel instance is required for tool resolution')
      throw new AgentInitializationException('Kernel instance is required for tool resolution.')
    }

    logger.debug(`Validating ${toolsList.length} tool(s)`)

    for (const tool of toolsList) {
      const toolId = tool.id
      if (!toolId || tool.type !== 'function') {
        continue
      }

      if (!toolId.includes('.')) {
        logger.error(`Tool id '${toolId}' must be in format PluginName.FunctionName`)
        throw new AgentInitializationException(`Tool id '${toolId}' must be in format PluginName.FunctionName`)
      }

      const [pluginName, functionName] = toolId.split('.', 2)

      const plugin = kernel.plugins.get(pluginName)
      if (!plugin) {
        logger.error(`Plugin '${pluginName}' not found in kernel`)
        throw new AgentInitializationException(`Plugin '${pluginName}' not found in kernel.`)
      }

      if (!plugin.functions.has(functionName)) {
        logger.error(`Function '${functionName}' not found in plugin '${pluginName}'`)
        throw new AgentInitializationException(`Function '${functionName}' not found in plugin '${pluginName}'.`)
      }
    }

    logger.debug('All tools validated successfully')
  }
}

// #endregion

// #region KernelPromptTemplate

/**
 * Basic kernel prompt template implementation.
 */
export class KernelPromptTemplate implements PromptTemplateBase {
  private template: string

  constructor(options: { template: string }) {
    this.template = options.template
  }

  async render(_kernel: Kernel, arguments_?: KernelArguments): Promise<string> {
    // Basic template rendering - in a real implementation, this would
    // support more sophisticated template syntax
    let result = this.template

    if (arguments_) {
      for (const [key, value] of Object.entries(arguments_)) {
        if (key !== 'executionSettings') {
          result = result.replace(new RegExp(`{{${key}}}`, 'g'), String(value))
        }
      }
    }

    return result
  }
}

// #endregion
