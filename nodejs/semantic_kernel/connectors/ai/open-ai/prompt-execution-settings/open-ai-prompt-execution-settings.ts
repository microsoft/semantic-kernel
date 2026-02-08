import { PromptExecutionSettings } from '../../prompt-execution-settings'

/**
 * Common request settings for (Azure) OpenAI services.
 */
export class OpenAIPromptExecutionSettings extends PromptExecutionSettings {
  /** The AI model ID (alias: model) */
  aiModelId?: string

  /** Frequency penalty (-2.0 to 2.0) */
  frequencyPenalty?: number

  /** Logit bias dictionary */
  logitBias?: Record<string | number, number>

  /** Maximum tokens to generate (must be > 0) */
  maxTokens?: number

  /** Number of responses to generate (1-128, alias: n) */
  numberOfResponses?: number

  /** Presence penalty (-2.0 to 2.0) */
  presencePenalty?: number

  /** Random seed for deterministic sampling */
  seed?: number

  /** Stop sequences */
  stop?: string | string[]

  /** Enable streaming */
  stream?: boolean

  /** Temperature (0.0 to 2.0) */
  temperature?: number

  /** Top-p sampling (0.0 to 1.0) */
  topP?: number

  /** User identifier */
  user?: string

  /** Store the request for future use */
  store?: boolean

  /** Metadata dictionary */
  metadata?: Record<string, string>

  constructor(options?: {
    aiModelId?: string
    frequencyPenalty?: number
    logitBias?: Record<string | number, number>
    maxTokens?: number
    numberOfResponses?: number
    presencePenalty?: number
    seed?: number
    stop?: string | string[]
    stream?: boolean
    temperature?: number
    topP?: number
    user?: string
    store?: boolean
    metadata?: Record<string, string>
    [key: string]: any
  }) {
    super(options)

    this.aiModelId = options?.aiModelId
    this.frequencyPenalty = options?.frequencyPenalty
    this.logitBias = options?.logitBias
    this.maxTokens = options?.maxTokens
    this.numberOfResponses = options?.numberOfResponses
    this.presencePenalty = options?.presencePenalty
    this.seed = options?.seed
    this.stop = options?.stop
    this.stream = options?.stream ?? false
    this.temperature = options?.temperature
    this.topP = options?.topP
    this.user = options?.user
    this.store = options?.store
    this.metadata = options?.metadata
  }

  /**
   * Prepare settings dictionary for the API request.
   * Converts TypeScript property names to snake_case API parameter names.
   */
  override prepareSettingsDict(kwargs?: Record<string, any>): Record<string, any> {
    const result = super.prepareSettingsDict(kwargs)

    // Map aiModelId to model
    if (this.aiModelId !== undefined && this.aiModelId !== null) {
      result.model = this.aiModelId
      delete result.aiModelId
    }

    // Map numberOfResponses to n
    if (this.numberOfResponses !== undefined && this.numberOfResponses !== null) {
      result.n = this.numberOfResponses
      delete result.numberOfResponses
    }

    // Convert camelCase to snake_case for other properties
    if (this.frequencyPenalty !== undefined) result.frequency_penalty = this.frequencyPenalty
    if (this.logitBias !== undefined) result.logit_bias = this.logitBias
    if (this.maxTokens !== undefined) result.max_tokens = this.maxTokens
    if (this.presencePenalty !== undefined) result.presence_penalty = this.presencePenalty
    if (this.topP !== undefined) result.top_p = this.topP

    // Remove camelCase versions
    delete result.frequencyPenalty
    delete result.logitBias
    delete result.maxTokens
    delete result.presencePenalty
    delete result.topP

    return result
  }
}

/**
 * Specific settings for the completions endpoint.
 */
export class OpenAITextPromptExecutionSettings extends OpenAIPromptExecutionSettings {
  /** The prompt text (set by the service, do not set manually) */
  prompt?: string

  /** Best of N completions (must be >= 1) */
  bestOf?: number

  /** Echo the prompt in the response */
  echo?: boolean

  /** Number of log probabilities to return (0-5) */
  logprobs?: number

  /** Suffix to append after completion */
  suffix?: string

  constructor(options?: {
    prompt?: string
    bestOf?: number
    echo?: boolean
    logprobs?: number
    suffix?: string
    [key: string]: any
  }) {
    super(options)

    this.prompt = options?.prompt
    this.bestOf = options?.bestOf
    this.echo = options?.echo ?? false
    this.logprobs = options?.logprobs
    this.suffix = options?.suffix

    // Validate bestOf and numberOfResponses
    this._checkBestOfAndN()
  }

  /**
   * Validate that bestOf is not less than numberOfResponses.
   */
  private _checkBestOfAndN(): void {
    const bestOf = this.bestOf ?? this.extensionData?.bestOf
    const numberOfResponses = this.numberOfResponses ?? this.extensionData?.numberOfResponses

    if (
      bestOf !== undefined &&
      bestOf !== null &&
      numberOfResponses !== undefined &&
      numberOfResponses !== null &&
      bestOf < numberOfResponses
    ) {
      throw new Error(
        'When used with numberOfResponses, bestOf controls the number of candidate completions and n specifies how many to return, therefore bestOf must be greater than numberOfResponses.'
      )
    }
  }

  override prepareSettingsDict(kwargs?: Record<string, any>): Record<string, any> {
    const result = super.prepareSettingsDict(kwargs)

    if (this.bestOf !== undefined) result.best_of = this.bestOf

    delete result.bestOf

    return result
  }
}

/**
 * Specific settings for the Chat Completion endpoint.
 */
export class OpenAIChatPromptExecutionSettings extends OpenAIPromptExecutionSettings {
  /** Response format configuration */
  responseFormat?: { type: 'text' | 'json_object' | 'json_schema'; [key: string]: any } | Record<string, any>

  /** Function call configuration (deprecated, use toolChoice) */
  functionCall?: string

  /** Functions list (deprecated, use tools) */
  functions?: Record<string, any>[]

  /** Messages (set by the service, do not set manually) */
  messages?: Record<string, any>[]

  /** Enable parallel tool calls */
  parallelToolCalls?: boolean

  /** Tools configuration (set by the service based on function choice configuration) */
  tools?: Record<string, any>[]

  /** Tool choice configuration (set by the service based on function choice configuration) */
  toolChoice?: string

  /** Structured JSON response flag (set by the service) */
  structuredJsonResponse?: boolean

  /** Stream options (set automatically when streaming) */
  streamOptions?: Record<string, any>

  /** Maximum completion tokens including output and reasoning tokens */
  maxCompletionTokens?: number

  /** Reasoning effort level (low/medium/high) */
  reasoningEffort?: 'low' | 'medium' | 'high'

  /** Extra body parameters */
  extraBody?: Record<string, any>

  constructor(options?: {
    responseFormat?: { type: 'text' | 'json_object' | 'json_schema'; [key: string]: any } | Record<string, any>
    functionCall?: string
    functions?: Record<string, any>[]
    messages?: Record<string, any>[]
    parallelToolCalls?: boolean
    tools?: Record<string, any>[]
    toolChoice?: string
    structuredJsonResponse?: boolean
    streamOptions?: Record<string, any>
    maxCompletionTokens?: number
    reasoningEffort?: 'low' | 'medium' | 'high'
    extraBody?: Record<string, any>
    [key: string]: any
  }) {
    super(options)

    this.responseFormat = options?.responseFormat
    this.functionCall = options?.functionCall
    this.functions = options?.functions
    this.messages = options?.messages
    this.parallelToolCalls = options?.parallelToolCalls
    this.tools = options?.tools
    this.toolChoice = options?.toolChoice
    this.structuredJsonResponse = options?.structuredJsonResponse ?? false
    this.streamOptions = options?.streamOptions
    this.maxCompletionTokens = options?.maxCompletionTokens
    this.reasoningEffort = options?.reasoningEffort
    this.extraBody = options?.extraBody

    // Validate deprecated function_call and functions
    this._validateFunctionCall()

    // Validate response format and set structured flag
    this._validateResponseFormat()
  }

  /**
   * Validate the function_call and functions parameters (deprecated).
   */
  private _validateFunctionCall(): void {
    if (this.functionCall !== undefined || this.functions !== undefined) {
      console.warn(
        'The functionCall and functions parameters are deprecated. Please use the toolChoice and tools parameters instead.'
      )
    }
  }

  /**
   * Validate response_format and set structuredJsonResponse flag.
   */
  private _validateResponseFormat(): void {
    if (!this.responseFormat) {
      return
    }

    if (typeof this.responseFormat === 'object') {
      if (this.responseFormat.type === 'json_object') {
        return
      }
      if (this.responseFormat.type === 'json_schema') {
        const jsonSchema = this.responseFormat.json_schema
        if (typeof jsonSchema === 'object' && jsonSchema !== null) {
          this.structuredJsonResponse = true
          return
        }
        throw new Error("If responseFormat has type 'json_schema', 'json_schema' must be a valid dictionary.")
      }
    }

    // If responseFormat is a class/type, assume structured JSON
    if (typeof this.responseFormat === 'function') {
      this.structuredJsonResponse = true
    } else if (typeof this.responseFormat !== 'object') {
      throw new Error('responseFormat must be a dictionary, a class/type, or undefined')
    }
  }

  override prepareSettingsDict(kwargs?: Record<string, any>): Record<string, any> {
    const result = super.prepareSettingsDict(kwargs)

    if (this.responseFormat !== undefined) result.response_format = this.responseFormat
    if (this.functionCall !== undefined) result.function_call = this.functionCall
    if (this.parallelToolCalls !== undefined) result.parallel_tool_calls = this.parallelToolCalls
    if (this.toolChoice !== undefined) result.tool_choice = this.toolChoice
    if (this.streamOptions !== undefined) result.stream_options = this.streamOptions
    if (this.maxCompletionTokens !== undefined) result.max_completion_tokens = this.maxCompletionTokens
    if (this.reasoningEffort !== undefined) result.reasoning_effort = this.reasoningEffort
    if (this.extraBody !== undefined) result.extra_body = this.extraBody

    // Remove camelCase versions
    delete result.responseFormat
    delete result.functionCall
    delete result.parallelToolCalls
    delete result.toolChoice
    delete result.streamOptions
    delete result.maxCompletionTokens
    delete result.reasoningEffort
    delete result.extraBody

    return result
  }
}

/**
 * Specific settings for the text embedding endpoint.
 */
export class OpenAIEmbeddingPromptExecutionSettings extends PromptExecutionSettings {
  /** Input text or tokens */
  input?: string | string[] | number[] | number[][]

  /** The AI model ID (alias: model) */
  aiModelId?: string

  /** Encoding format for embeddings */
  encodingFormat?: 'float' | 'base64'

  /** User identifier */
  user?: string

  /** Extra headers */
  extraHeaders?: Record<string, any>

  /** Extra query parameters */
  extraQuery?: Record<string, any>

  /** Extra body parameters */
  extraBody?: Record<string, any>

  /** Request timeout */
  timeout?: number

  /** Embedding dimensions (1-3072) */
  dimensions?: number

  constructor(options?: {
    input?: string | string[] | number[] | number[][]
    aiModelId?: string
    encodingFormat?: 'float' | 'base64'
    user?: string
    extraHeaders?: Record<string, any>
    extraQuery?: Record<string, any>
    extraBody?: Record<string, any>
    timeout?: number
    dimensions?: number
    [key: string]: any
  }) {
    super(options)

    this.input = options?.input
    this.aiModelId = options?.aiModelId
    this.encodingFormat = options?.encodingFormat
    this.user = options?.user
    this.extraHeaders = options?.extraHeaders
    this.extraQuery = options?.extraQuery
    this.extraBody = options?.extraBody
    this.timeout = options?.timeout
    this.dimensions = options?.dimensions
  }

  override prepareSettingsDict(kwargs?: Record<string, any>): Record<string, any> {
    const result = super.prepareSettingsDict(kwargs)

    // Map aiModelId to model
    if (this.aiModelId !== undefined && this.aiModelId !== null) {
      result.model = this.aiModelId
      delete result.aiModelId
    }

    if (this.encodingFormat !== undefined) result.encoding_format = this.encodingFormat
    if (this.extraHeaders !== undefined) result.extra_headers = this.extraHeaders
    if (this.extraQuery !== undefined) result.extra_query = this.extraQuery
    if (this.extraBody !== undefined) result.extra_body = this.extraBody

    // Remove camelCase versions
    delete result.encodingFormat
    delete result.extraHeaders
    delete result.extraQuery
    delete result.extraBody

    return result
  }
}
