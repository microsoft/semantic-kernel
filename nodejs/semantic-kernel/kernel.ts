/**
 * The Kernel of Semantic Kernel.
 *
 * This is the main entry point for Semantic Kernel. It provides the ability to run
 * functions and manage filters, plugins, and AI services.
 */

import { EventEmitter } from 'events'
import { ChatMessageContent } from './contents/chat-message-content'
import { KernelArguments as KernelArgumentsClass } from './functions/kernel-arguments'
import { KernelFunctionFromPrompt } from './functions/kernel-function-from-prompt'
import { PromptTemplateConfig as PromptTemplateConfigClass } from './prompt-template/prompt-template-config'
import { createDefaultLogger, Logger, LoggerOptions } from './utils/logger'

// Type definitions for core Kernel components
export interface KernelPlugin {
  name: string
  description?: string
  functions: Map<string, KernelFunction>
}

export interface KernelFunction {
  name: string
  pluginName?: string
  description?: string
  parameters: KernelParameter[]
  metadata: KernelFunctionMetadata
  invoke(kernel: Kernel, arguments_: KernelArguments, metadata?: Record<string, any>): Promise<FunctionResult>
  invokeStream?(kernel: Kernel, arguments_: KernelArguments): AsyncGenerator<StreamingContentMixin[] | FunctionResult>
}

export interface KernelParameter {
  name: string
  description?: string
  defaultValue?: any
  type?: string
  isRequired: boolean
}

export interface KernelFunctionMetadata {
  name: string
  pluginName?: string
  description?: string
  parameters: KernelParameter[]
  returnParameter?: {
    description?: string
    type?: string
  }
}

// Using actual KernelArguments class from ./functions/kernel-arguments
export type KernelArguments = KernelArgumentsClass

export interface FunctionResult {
  function: KernelFunctionMetadata
  value: any
  metadata?: Record<string, any>
}

export interface StreamingContentMixin {
  choiceIndex: number
  content?: string
  metadata?: Record<string, any>
}

export interface ChatHistory {
  messages: ChatMessage[]
  addMessage(message: ChatMessage): void
}

export interface ChatMessage {
  role: string
  content: string
  metadata?: Record<string, any>
}

export interface FunctionCallContent {
  id?: string
  name?: string
  pluginName?: string
  functionName?: string
  arguments?: string
  index?: number
  metadata?: Record<string, any>
  toKernelArguments(): KernelArguments
}

export interface FunctionResultContent {
  result: any
  functionCallContent?: FunctionCallContent
  toChatMessageContent(): ChatMessage
  toStreamingChatMessageContent(): ChatMessage
}

export interface PromptExecutionSettings {
  serviceId?: string
  modelId?: string
  temperature?: number
  topP?: number
  maxTokens?: number
  [key: string]: any
}

// Using actual PromptTemplateConfig class from ./prompt-template/prompt-template-config
export type PromptTemplateConfig = PromptTemplateConfigClass

export interface AIServiceClient {
  serviceId?: string
  getModelId?(): string
}

export interface EmbeddingGeneratorBase extends AIServiceClient {
  generateRawEmbeddings(texts: string[], settings?: PromptExecutionSettings, ...kwargs: any[]): Promise<number[][]>
}

export interface AIServiceSelector {
  selectAIService(
    kernel: Kernel,
    function_: KernelFunction,
    arguments_: KernelArguments
  ): Promise<[AIServiceClient | null, PromptExecutionSettings | null]>
}

export interface FunctionChoiceBehavior {
  filters?: any
}

// Filter types
export enum FilterTypes {
  FUNCTION_INVOCATION = 'function_invocation',
  PROMPT_RENDERING = 'prompt_rendering',
  AUTO_FUNCTION_INVOCATION = 'auto_function_invocation',
}

export interface FunctionInvocationContext {
  function: KernelFunction
  kernel: Kernel
  arguments: KernelArguments
  result?: FunctionResult
  metadata?: Record<string, any>
}

export interface AutoFunctionInvocationContext {
  function: KernelFunction
  kernel: Kernel
  arguments: KernelArguments
  isStreaming: boolean
  chatHistory: ChatHistory
  functionCallContent?: FunctionCallContent
  executionSettings?: PromptExecutionSettings
  functionResult?: FunctionResult
  functionCount: number
  requestSequenceIndex: number
  functionSequenceIndex?: number
  terminate?: boolean
}

export type Filter<T> = (context: T, next: () => Promise<void>) => Promise<void>

// Kernel configuration options
export interface KernelOptions {
  plugins?: KernelPlugin | KernelPlugin[] | Record<string, KernelPlugin>
  services?: AIServiceClient | AIServiceClient[] | Record<string, AIServiceClient>
  aiServiceSelector?: AIServiceSelector
  functionInvocationFilters?: Filter<FunctionInvocationContext>[]
  promptRenderingFilters?: Filter<any>[]
  autoFunctionInvocationFilters?: Filter<AutoFunctionInvocationContext>[]
  logger?: Logger
  loggerOptions?: LoggerOptions
}

/**
 * Main Kernel class that manages plugins, services, and execution
 */
export class Kernel extends EventEmitter {
  private _plugins: Map<string, KernelPlugin>
  private _services: Map<string, AIServiceClient>
  private _aiServiceSelector?: AIServiceSelector
  private _functionInvocationFilters: Filter<FunctionInvocationContext>[]
  private _promptRenderingFilters: Filter<any>[]
  private _autoFunctionInvocationFilters: Filter<AutoFunctionInvocationContext>[]
  private _logger: Logger

  constructor(options: KernelOptions = {}) {
    super()

    // Initialize logger
    this._logger = options.logger || createDefaultLogger('Kernel', options.loggerOptions)

    // Initialize plugins
    this._plugins = new Map()
    if (options.plugins) {
      this._initializePlugins(options.plugins)
    }

    // Initialize services
    this._services = new Map()
    if (options.services) {
      this._initializeServices(options.services)
    }

    this._aiServiceSelector = options.aiServiceSelector
    this._functionInvocationFilters = options.functionInvocationFilters || []
    this._promptRenderingFilters = options.promptRenderingFilters || []
    this._autoFunctionInvocationFilters = options.autoFunctionInvocationFilters || []
  }

  // Logger access
  get logger(): Logger {
    return this._logger
  }

  // Plugin management
  get plugins(): Map<string, KernelPlugin> {
    return this._plugins
  }

  private _initializePlugins(plugins: KernelPlugin | KernelPlugin[] | Record<string, KernelPlugin>): void {
    if (Array.isArray(plugins)) {
      plugins.forEach((plugin) => this._plugins.set(plugin.name, plugin))
    } else if ('name' in plugins) {
      this._plugins.set(plugins.name as string, plugins as KernelPlugin)
    } else {
      Object.entries(plugins).forEach(([name, plugin]) => {
        this._plugins.set(name, plugin)
      })
    }
  }

  addPlugin(plugin: KernelPlugin): void {
    this._plugins.set(plugin.name, plugin)
    this._logger.debug(`Added plugin: ${plugin.name}`)
  }

  getPlugin(pluginName: string): KernelPlugin {
    const plugin = this._plugins.get(pluginName)
    if (!plugin) {
      this._logger.error(`Plugin '${pluginName}' not found`)
      throw new Error(`Plugin '${pluginName}' not found`)
    }
    return plugin
  }

  getFunction(pluginName: string, functionName: string): KernelFunction {
    const plugin = this.getPlugin(pluginName)
    const func = plugin.functions.get(functionName)
    if (!func) {
      this._logger.error(`Function '${functionName}' not found in plugin '${pluginName}'`)
      throw new Error(`Function '${functionName}' not found in plugin '${pluginName}'`)
    }
    return func
  }

  getFullListOfFunctionMetadata(): KernelFunctionMetadata[] {
    /**
     * Get a list of all function metadata in the plugins.
     */
    if (!this._plugins || this._plugins.size === 0) {
      return []
    }
    const metadata: KernelFunctionMetadata[] = []
    for (const plugin of this._plugins.values()) {
      for (const func of plugin.functions.values()) {
        metadata.push(func.metadata)
      }
    }
    return metadata
  }

  // Service management
  get services(): Map<string, AIServiceClient> {
    return this._services
  }

  private _initializeServices(services: AIServiceClient | AIServiceClient[] | Record<string, AIServiceClient>): void {
    if (Array.isArray(services)) {
      services.forEach((service, index) => {
        const serviceId = service.serviceId || `service_${index}`
        this._services.set(serviceId, service)
      })
    } else if ('serviceId' in services || typeof services === 'object') {
      const serviceId = (services as AIServiceClient).serviceId || 'default'
      this._services.set(serviceId, services as AIServiceClient)
    } else {
      Object.entries(services).forEach(([id, service]) => {
        this._services.set(id, service as AIServiceClient)
      })
    }
  }

  addService(serviceId: string, service: AIServiceClient): void {
    this._services.set(serviceId, service)
    this._logger.debug(`Added service: ${serviceId}`)
  }

  getService<T extends AIServiceClient>(serviceId?: string, type?: new (...args: any[]) => T): T | null {
    if (serviceId) {
      const service = this._services.get(serviceId)
      if (service && (!type || service instanceof type)) {
        return service as T
      }
    }

    // If no serviceId provided or not found, find first service of type
    if (type) {
      for (const service of this._services.values()) {
        if (service instanceof type) {
          return service as T
        }
      }
    }

    return null
  }

  // Function invocation
  async invoke(options: {
    function?: KernelFunction
    arguments?: KernelArguments
    functionName?: string
    pluginName?: string
    metadata?: Record<string, any>
    [key: string]: any
  }): Promise<FunctionResult | null> {
    let { function: func, arguments: args } = options
    const { function: _func, arguments: _args, functionName, pluginName, metadata, ...kwargs } = options

    // Ensure args is a KernelArguments instance
    if (!args || !(args instanceof KernelArgumentsClass)) {
      const newArgs = new KernelArgumentsClass()
      if (args) {
        // If args is a plain object, copy its properties
        if (typeof args === 'object') {
          for (const [key, value] of Object.entries(args)) {
            newArgs.set(key, value)
          }
        }
      }
      args = newArgs
    }
    // Merge kwargs into arguments
    for (const [key, value] of Object.entries(kwargs)) {
      args.set(key, value)
    }

    if (!func) {
      if (!functionName || !pluginName) {
        this._logger.error('No function, or function name and plugin name provided')
        throw new Error('No function, or function name and plugin name provided')
      }
      func = this.getFunction(pluginName, functionName)
    }

    try {
      return await func.invoke(this, args, metadata)
    } catch (error) {
      if (error instanceof Error && error.name === 'OperationCancelledException') {
        this._logger.info(`Operation cancelled during function invocation: ${error.message}`)
        return null
      }
      this._logger.error(
        `Something went wrong in function invocation. During function invocation: ` +
          `'${func.pluginName}.${func.name}'. Error: ${error}`
      )
      throw new Error(`Error occurred while invoking function: '${func.pluginName}.${func.name}'`, { cause: error })
    }
  }

  async *invokeStream(options: {
    function?: KernelFunction
    arguments?: KernelArguments
    functionName?: string
    pluginName?: string
    metadata?: Record<string, any>
    returnFunctionResults?: boolean
    [key: string]: any
  }): AsyncGenerator<StreamingContentMixin[] | FunctionResult> {
    let { function: func, arguments: args, returnFunctionResults } = options
    const {
      function: _func,
      arguments: _args,
      returnFunctionResults: _returnFunctionResults,
      functionName,
      pluginName,
      metadata: _metadata,
      ...kwargs
    } = options

    // Ensure args is a KernelArguments instance
    if (!args || !(args instanceof KernelArgumentsClass)) {
      const newArgs = new KernelArgumentsClass()
      if (args) {
        // If args is a plain object, copy its properties
        if (typeof args === 'object') {
          for (const [key, value] of Object.entries(args)) {
            newArgs.set(key, value)
          }
        }
      }
      args = newArgs
    }

    // Merge kwargs into arguments
    for (const [key, value] of Object.entries(kwargs)) {
      args.set(key, value)
    }

    returnFunctionResults = returnFunctionResults ?? false

    if (!func) {
      if (!functionName || !pluginName) {
        this._logger.error('No function(s) or function- and plugin-name provided')
        throw new Error('No function(s) or function- and plugin-name provided')
      }
      func = this.getFunction(pluginName, functionName)
    }

    if (!func.invokeStream) {
      this._logger.error(`Function '${func.name}' does not support streaming`)
      throw new Error(`Function '${func.name}' does not support streaming`)
    }

    const functionResult: Array<StreamingContentMixin[] | any> = []

    for await (const streamMessage of func.invokeStream(this, args)) {
      if (this._isFunctionResult(streamMessage) && streamMessage.metadata?.exception) {
        this._logger.error(`Error occurred while invoking function: '${func.pluginName}.${func.name}'`, {
          exception: streamMessage.metadata.exception,
        })
        throw new Error(`Error occurred while invoking function: '${func.pluginName}.${func.name}'`, {
          cause: streamMessage.metadata.exception,
        })
      }
      functionResult.push(streamMessage)
      yield streamMessage
    }

    if (returnFunctionResults) {
      const outputFunctionResult: StreamingContentMixin[] = []
      for (const result of functionResult) {
        for (const choice of result) {
          if (!this._isStreamingContent(choice)) {
            continue
          }
          if (outputFunctionResult.length <= choice.choiceIndex) {
            outputFunctionResult.push({ ...choice })
          } else {
            // Merge content
            const existing = outputFunctionResult[choice.choiceIndex]
            existing.content = (existing.content || '') + (choice.content || '')
          }
        }
      }
      yield {
        function: func.metadata,
        value: outputFunctionResult,
      }
    }
  }

  async invokePrompt(options: {
    prompt: string
    functionName?: string
    pluginName?: string
    arguments?: KernelArguments
    templateFormat?: 'semantic-kernel' | 'handlebars' | 'jinja2'
    promptTemplateConfig?: PromptTemplateConfig
    [key: string]: any
  }): Promise<FunctionResult | null> {
    const {
      prompt,
      functionName,
      pluginName,
      arguments: args,
      templateFormat,
      promptTemplateConfig,
      ...kwargs
    } = options

    // Ensure args is a KernelArguments instance
    let finalArgs: KernelArguments
    if (!args || !(args instanceof KernelArgumentsClass)) {
      finalArgs = new KernelArgumentsClass()
      if (args) {
        // If args is a plain object, copy its properties
        if (typeof args === 'object') {
          for (const [key, value] of Object.entries(args)) {
            finalArgs.set(key, value)
          }
        }
      }
    } else {
      finalArgs = args
    }
    for (const [key, value] of Object.entries(kwargs)) {
      finalArgs.set(key, value)
    }

    if (!prompt) {
      this._logger.error('The prompt is either null or empty.')
      throw new Error('The prompt is either null or empty.')
    }

    // Create a function from prompt using KernelFunctionFromPrompt
    const func = new KernelFunctionFromPrompt({
      functionName: functionName || this._generateRandomName(),
      pluginName,
      prompt,
      templateFormat,
      promptTemplateConfig,
    })

    return await this.invoke({ function: func, arguments: finalArgs })
  }

  async *invokePromptStream(options: {
    prompt: string
    functionName?: string
    pluginName?: string
    arguments?: KernelArguments
    templateFormat?: 'semantic-kernel' | 'handlebars' | 'jinja2'
    returnFunctionResults?: boolean
    promptTemplateConfig?: PromptTemplateConfig
    [key: string]: any
  }): AsyncGenerator<StreamingContentMixin[] | FunctionResult> {
    const {
      prompt,
      functionName,
      pluginName,
      arguments: args,
      templateFormat,
      _returnFunctionResults,
      promptTemplateConfig,
      ...kwargs
    } = options

    // Ensure args is a KernelArguments instance
    let finalArgs: KernelArguments
    if (!args || !(args instanceof KernelArgumentsClass)) {
      finalArgs = new KernelArgumentsClass()
      if (args) {
        // If args is a plain object, copy its properties
        if (typeof args === 'object') {
          for (const [key, value] of Object.entries(args)) {
            finalArgs.set(key, value)
          }
        }
      }
    } else {
      finalArgs = args
    }
    for (const [key, value] of Object.entries(kwargs)) {
      finalArgs.set(key, value)
    }

    if (!prompt) {
      this._logger.error('The prompt is either null or empty.')
      throw new Error('The prompt is either null or empty.')
    }

    // Create a function from prompt using KernelFunctionFromPrompt
    const func = new KernelFunctionFromPrompt({
      functionName: functionName || this._generateRandomName(),
      pluginName,
      prompt,
      templateFormat,
      promptTemplateConfig,
    })

    // Use the function's invokeStream method
    yield* func.invokeStream(this, finalArgs)
  }

  async invokeFunctionCall(options: {
    functionCall: FunctionCallContent
    chatHistory: ChatHistory
    arguments?: KernelArguments
    executionSettings?: PromptExecutionSettings
    functionCallCount?: number
    requestIndex?: number
    isStreaming?: boolean
    functionBehavior?: FunctionChoiceBehavior
  }): Promise<AutoFunctionInvocationContext | null> {
    const {
      functionCall,
      chatHistory,
      arguments: args,
      executionSettings,
      functionCallCount,
      requestIndex,
      isStreaming,
      functionBehavior,
    } = options

    try {
      if (!functionCall.name) {
        this._logger.error('The function name is required.')
        throw new Error('The function name is required.')
      }

      // Validate function is in allowed list if function_behavior.filters is provided
      if (functionBehavior?.filters) {
        const allowedFunctions = this._getFilteredFunctionNames(functionBehavior.filters)
        const fullyQualifiedName = functionCall.pluginName
          ? `${functionCall.pluginName}-${functionCall.functionName || functionCall.name}`
          : functionCall.functionName || functionCall.name
        if (!allowedFunctions.includes(fullyQualifiedName)) {
          const errorMsg = `Only functions: [${allowedFunctions.join(', ')}] are allowed, ${fullyQualifiedName} is not allowed.`
          this._logger.error(errorMsg)
          throw new Error(errorMsg)
        }
      }

      // Get the function to call
      const functionToCall = this.getFunction(
        functionCall.pluginName || '',
        functionCall.functionName || functionCall.name
      )

      // Ensure args is a KernelArguments instance before cloning
      let argsCloned: KernelArguments
      if (!args || !(args instanceof KernelArgumentsClass)) {
        argsCloned = new KernelArgumentsClass()
        if (args) {
          // If args is a plain object, copy its properties
          if (typeof args === 'object') {
            for (const [key, value] of Object.entries(args)) {
              argsCloned.set(key, value)
            }
          }
        }
      } else {
        argsCloned = args.merge({})
      }
      let parsedArgs: KernelArguments | null = null

      try {
        parsedArgs = functionCall.toKernelArguments()
      } catch (error) {
        this._logger.info(
          `Received invalid arguments for function ${functionCall.name}: ${error}. Trying tool call again.`
        )
        chatHistory.addMessage(
          new ChatMessageContent({
            role: 'tool' as any,
            content: 'The tool call arguments are malformed. Arguments must be in JSON format. Please try again.',
            metadata: { functionCall },
          })
        )
        return null
      }

      // Check for missing or unexpected parameters
      const requiredParamNames = new Set(functionToCall.parameters.filter((p) => p.isRequired).map((p) => p.name))
      const receivedParamNames = new Set(Object.keys(parsedArgs || {}))

      const missingParams = [...requiredParamNames].filter((p) => !receivedParamNames.has(p))
      const allParamNames = new Set(functionToCall.parameters.map((p) => p.name))
      const unexpectedParams = [...receivedParamNames].filter((p) => !allParamNames.has(p))

      if (missingParams.length > 0 || unexpectedParams.length > 0) {
        const msgParts: string[] = []
        if (missingParams.length > 0) {
          msgParts.push(`Missing required argument(s): ${missingParams.sort().join(', ')}.`)
        }
        if (unexpectedParams.length > 0) {
          msgParts.push(`Received unexpected argument(s): ${unexpectedParams.sort().join(', ')}.`)
        }
        const msg = msgParts.join(' ') + ' Please revise the arguments to match the function signature.'

        this._logger.info(msg)
        chatHistory.addMessage(
          new ChatMessageContent({
            role: 'tool' as any,
            content: msg,
            metadata: { functionCall },
          })
        )
        return null
      }

      // Validate parameter count
      const numRequiredParams = functionToCall.parameters.filter((p) => p.isRequired).length
      if (parsedArgs === null || Object.keys(parsedArgs).length < numRequiredParams) {
        const msg =
          `There are \`${numRequiredParams}\` tool call arguments required and ` +
          `only \`${parsedArgs ? Object.keys(parsedArgs).length : 0}\` received. The required arguments are: ` +
          `[${functionToCall.parameters
            .filter((p) => p.isRequired)
            .map((p) => p.name)
            .join(', ')}]. ` +
          'Please provide the required arguments and try again.'
        this._logger.info(msg)
        chatHistory.addMessage(
          new ChatMessageContent({
            role: 'tool' as any,
            content: msg,
            metadata: { functionCall },
          })
        )
        return null
      }

      if (parsedArgs) {
        argsCloned.mergeInPlace(parsedArgs)
      }

      this._logger.info(`Calling ${functionCall.name} function with args: ${functionCall.arguments}`)

      const invocationContext: AutoFunctionInvocationContext = {
        function: functionToCall,
        kernel: this,
        arguments: argsCloned,
        isStreaming: isStreaming || false,
        chatHistory,
        functionCallContent: functionCall,
        executionSettings,
        functionResult: {
          function: functionToCall.metadata,
          value: null,
        },
        functionCount: functionCallCount || 0,
        requestSequenceIndex: requestIndex || 0,
      }

      if (functionCall.index !== undefined) {
        invocationContext.functionSequenceIndex = functionCall.index
      }

      // Execute filters and function
      await this._executeAutoFunctionInvocation(invocationContext)

      // Snapshot the tool's return value so later mutations don't leak back
      if (invocationContext.functionResult && invocationContext.functionResult.value !== null) {
        invocationContext.functionResult.value = this._deepCopy(invocationContext.functionResult.value)
      }

      // Detect if streaming based on chat history
      const isActuallyStreaming = chatHistory.messages.some((msg) => msg.metadata?.streaming === true)

      // Add result to chat history
      chatHistory.addMessage(
        new ChatMessageContent({
          role: 'tool' as any,
          content: JSON.stringify(invocationContext.functionResult?.value),
          metadata: {
            functionCall,
            functionResult: invocationContext.functionResult,
            streaming: isActuallyStreaming,
          },
        })
      )

      return invocationContext.terminate ? null : invocationContext
    } catch (error) {
      this._logger.error(`The function '${functionCall.name}' is not part of the provided functions: ${error}`)
      chatHistory.addMessage(
        new ChatMessageContent({
          role: 'tool' as any,
          content:
            `The tool call with name '${functionCall.name}' is not part of the provided tools, ` +
            'please try again with a supplied tool call name and make sure to validate the name.',
          metadata: { functionCall, error },
        })
      )
      return null
    }
  }

  private async _executeAutoFunctionInvocation(context: AutoFunctionInvocationContext): Promise<void> {
    // Build filter stack
    const filters = [...this._autoFunctionInvocationFilters]

    // Execute filters in order
    let index = 0
    const next = async (): Promise<void> => {
      if (index < filters.length) {
        const filter = filters[index++]
        await filter(context, next)
      } else {
        // Execute the actual function
        await this._innerAutoFunctionInvokeHandler(context)
      }
    }

    await next()
  }

  private async _innerAutoFunctionInvokeHandler(context: AutoFunctionInvocationContext): Promise<void> {
    try {
      // Merge metadata with function call content
      const metadata = context.functionCallContent
        ? {
            ...context.functionCallContent.metadata,
            id: context.functionCallContent.id,
            name: context.functionCallContent.name,
            pluginName: context.functionCallContent.pluginName,
            functionName: context.functionCallContent.functionName,
            arguments: context.functionCallContent.arguments,
            index: context.functionCallContent.index,
          }
        : undefined

      const result = await context.function.invoke(context.kernel, context.arguments, metadata)
      if (result) {
        context.functionResult = result
      }
    } catch (error) {
      this._logger.error(`Error invoking function ${context.function.pluginName}.${context.function.name}: ${error}`)
      const value = `An error occurred while invoking the function ${context.function.pluginName}.${context.function.name}: ${error}`
      if (context.functionResult) {
        context.functionResult.value = value
      } else {
        context.functionResult = {
          function: context.function.metadata,
          value,
          metadata: { exception: error },
        }
      }
    }
  }

  async addEmbeddingToObject<T>(options: {
    inputs: T | T[]
    fieldToEmbed: string
    fieldToStore: string
    executionSettings: Record<string, PromptExecutionSettings>
    containerMode?: boolean
    castFunction?: (vector: number[]) => any
  }): Promise<void> {
    const { inputs, fieldToEmbed, fieldToStore, executionSettings, containerMode, castFunction } = options

    // Gather all fields to embed
    const contents: any[] = []
    const isArray = Array.isArray(inputs)

    if (containerMode) {
      contents.push(...(inputs as any)[fieldToEmbed])
    } else if (isArray) {
      for (const record of inputs) {
        contents.push((record as any)[fieldToEmbed])
      }
    } else {
      contents.push((inputs as any)[fieldToEmbed])
    }

    // Generate embeddings
    let vectors: number[][] | null = null
    let service: EmbeddingGeneratorBase | null = null

    for (const [serviceId, settings] of Object.entries(executionSettings)) {
      const candidate = this.getService(serviceId)
      if (candidate && 'generateRawEmbeddings' in candidate) {
        service = candidate as EmbeddingGeneratorBase
        vectors = await service.generateRawEmbeddings(contents, settings)
        break
      }
    }

    if (!service) {
      this._logger.error('No service found to generate embeddings.')
      throw new Error('No service found to generate embeddings.')
    }
    if (!vectors) {
      this._logger.error('No vectors were generated.')
      throw new Error('No vectors were generated.')
    }

    // Apply cast function if provided
    const finalVectors = castFunction ? vectors.map(castFunction) : vectors

    // Store embeddings
    if (containerMode) {
      ;(inputs as any)[fieldToStore] = finalVectors
    } else if (isArray) {
      ;(inputs as any[]).forEach((record, index) => {
        record[fieldToStore] = finalVectors[index]
      })
    } else {
      ;(inputs as any)[fieldToStore] = finalVectors[0]
    }
  }

  clone(): Kernel {
    /**
     * Clone the kernel instance to create a new one that may be mutated without affecting the current instance.
     *
     * Note: The same service clients are used in the new instance, so if you mutate the service clients
     * in the new instance, the original instance will be affected as well.
     *
     * Important: Functions are cloned by deep-copying metadata while retaining callable references.
     * This avoids attempting to clone unpickleable objects (e.g., async generators).
     */
    const clonedPlugins = new Map<string, KernelPlugin>()
    for (const [name, plugin] of this._plugins.entries()) {
      const clonedFunctions = new Map<string, KernelFunction>()
      for (const [funcName, func] of plugin.functions.entries()) {
        // Deep copy metadata but keep callable (invoke, invokeStream) as shallow reference
        clonedFunctions.set(funcName, {
          ...func,
          metadata: this._deepCopy(func.metadata),
          parameters: this._deepCopy(func.parameters),
          // Keep invoke and invokeStream as shallow references
        })
      }
      clonedPlugins.set(name, {
        name: plugin.name,
        description: plugin.description,
        functions: clonedFunctions,
      })
    }

    return new Kernel({
      plugins: Object.fromEntries(clonedPlugins),
      // Shallow copy of services, as they are not serializable
      services: Object.fromEntries(this._services),
      aiServiceSelector: this._deepCopy(this._aiServiceSelector),
      functionInvocationFilters: this._deepCopy(this._functionInvocationFilters),
      promptRenderingFilters: this._deepCopy(this._promptRenderingFilters),
      autoFunctionInvocationFilters: this._deepCopy(this._autoFunctionInvocationFilters),
      // Share the same logger instance
      logger: this._logger,
    })
  }

  // Helper methods
  private _generateRandomName(): string {
    return `func_${Math.random().toString(36).substring(2, 15)}`
  }

  private _deepCopy<T>(obj: T): T {
    if (obj === null || typeof obj !== 'object') {
      return obj
    }
    if (obj instanceof Date) {
      return new Date(obj.getTime()) as T
    }
    if (obj instanceof Array) {
      return obj.map((item) => this._deepCopy(item)) as T
    }
    if (obj instanceof Map) {
      const copy = new Map()
      obj.forEach((value, key) => {
        copy.set(key, this._deepCopy(value))
      })
      return copy as T
    }
    if (obj instanceof Set) {
      const copy = new Set()
      obj.forEach((value) => {
        copy.add(this._deepCopy(value))
      })
      return copy as T
    }
    if (typeof obj === 'object') {
      const copy: any = {}
      for (const key in obj) {
        if (Object.hasOwn(obj, key)) {
          copy[key] = this._deepCopy((obj as any)[key])
        }
      }
      return copy as T
    }
    return obj
  }

  private _getFilteredFunctionNames(filters: {
    included_plugins?: string[]
    excluded_plugins?: string[]
    included_functions?: string[]
    excluded_functions?: string[]
  }): string[] {
    // Helper to get list of allowed function names based on filters
    const includedPlugins = filters.included_plugins
    const excludedPlugins = filters.excluded_plugins || []
    const includedFunctions = filters.included_functions
    const excludedFunctions = filters.excluded_functions || []

    // Validate mutually exclusive filters
    if (includedPlugins && excludedPlugins.length > 0) {
      throw new Error('Cannot use both included_plugins and excluded_plugins at the same time.')
    }
    if (includedFunctions && excludedFunctions.length > 0) {
      throw new Error('Cannot use both included_functions and excluded_functions at the same time.')
    }

    const result: string[] = []
    for (const [pluginName, plugin] of this._plugins.entries()) {
      // Check plugin filters
      if (excludedPlugins.includes(pluginName) || (includedPlugins && !includedPlugins.includes(pluginName))) {
        continue
      }

      for (const [funcName, _func] of plugin.functions.entries()) {
        const fullyQualifiedName = `${pluginName}-${funcName}`

        // Check function filters
        if (
          excludedFunctions.includes(fullyQualifiedName) ||
          (includedFunctions && !includedFunctions.includes(fullyQualifiedName))
        ) {
          continue
        }

        result.push(fullyQualifiedName)
      }
    }
    return result
  }

  private _isFunctionResult(obj: any): obj is FunctionResult {
    return obj && typeof obj === 'object' && 'function' in obj && 'value' in obj
  }

  private _isStreamingContent(obj: any): obj is StreamingContentMixin {
    return obj && typeof obj === 'object' && 'choiceIndex' in obj
  }

  // Filter management
  addFunctionInvocationFilter(filter: Filter<FunctionInvocationContext>): void {
    this._functionInvocationFilters.push(filter)
  }

  addPromptRenderingFilter(filter: Filter<any>): void {
    this._promptRenderingFilters.push(filter)
  }

  addAutoFunctionInvocationFilter(filter: Filter<AutoFunctionInvocationContext>): void {
    this._autoFunctionInvocationFilters.push(filter)
  }

  constructCallStack<T>(
    filterType: FilterTypes,
    innerFunction: (context: T) => Promise<void>
  ): (context: T) => Promise<void> {
    let filters: Filter<T>[]

    switch (filterType) {
      case FilterTypes.FUNCTION_INVOCATION:
        filters = this._functionInvocationFilters as Filter<T>[]
        break
      case FilterTypes.PROMPT_RENDERING:
        filters = this._promptRenderingFilters as Filter<T>[]
        break
      case FilterTypes.AUTO_FUNCTION_INVOCATION:
        filters = this._autoFunctionInvocationFilters as Filter<T>[]
        break
      default:
        filters = []
    }

    return async (context: T) => {
      let index = 0
      const next = async (): Promise<void> => {
        if (index < filters.length) {
          const filter = filters[index++]
          await filter(context, next)
        } else {
          await innerFunction(context)
        }
      }
      await next()
    }
  }
}

// Export main class as default
export default Kernel
