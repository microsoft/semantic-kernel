import { randomUUID } from 'crypto'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { AuthorRole } from '../../contents/utils/author-role'
import { Agent } from '../agent'
import { CancellationToken } from '../runtime/core/cancellation-token'
import { CoreRuntime } from '../runtime/core/core-runtime'

/**
 * Default type alias for messages
 */
export type DefaultTypeAlias = ChatMessageContent | ChatMessageContent[]

/**
 * The result of an invocation of an orchestration.
 */
export class OrchestrationResult<TOut = DefaultTypeAlias> {
  public backgroundTask?: Promise<void>
  public value?: TOut
  public exception?: Error
  public cancellationToken: CancellationToken

  private _event: Promise<void>
  private _resolveEvent!: () => void

  constructor() {
    this.cancellationToken = new CancellationToken()
    this._event = new Promise<void>((resolve) => {
      this._resolveEvent = resolve
    })
  }

  /**
   * Get the result of the invocation.
   * If a timeout is specified, the method will wait for the result for the specified time.
   * If the result is not available within the timeout, a TimeoutError will be raised but the
   * invocation will not be aborted.
   *
   * @param timeout - The timeout (milliseconds) for getting the result. If undefined, wait indefinitely.
   * @returns The result of the invocation
   */
  async get(timeout?: number): Promise<TOut> {
    if (timeout !== undefined) {
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Timeout waiting for result')), timeout)
      )
      await Promise.race([this._event, timeoutPromise])
    } else {
      await this._event
    }

    if (this.value === undefined) {
      if (this.cancellationToken.isCancelled()) {
        throw new Error('The invocation was canceled before it could complete.')
      }
      if (this.exception) {
        throw this.exception
      }
      throw new Error('The invocation did not produce a result.')
    }
    return this.value
  }

  /**
   * Cancel the invocation.
   * This method will cancel the invocation.
   * Actors that have received messages will continue to process them, but no new messages will be processed.
   */
  cancel(): void {
    if (this.cancellationToken.isCancelled()) {
      throw new Error('The invocation has already been canceled.')
    }
    if (this.value !== undefined || this.exception !== undefined) {
      throw new Error('The invocation has already been completed.')
    }

    this.cancellationToken.cancel()
    this._resolveEvent()
  }

  /**
   * Internal method to set the result
   */
  _setResult(value: TOut): void {
    this.value = value
    this._resolveEvent()
  }

  /**
   * Internal method to set an exception
   */
  _setException(exception: Error): void {
    this.exception = exception
    this._resolveEvent()
  }
}

/**
 * Base class for multi-agent orchestration.
 */
export abstract class OrchestrationBase<TIn = DefaultTypeAlias, TOut = DefaultTypeAlias> {
  protected _members: Agent[]
  public name: string
  public description: string

  protected _inputTransform: (input: TIn) => DefaultTypeAlias | Promise<DefaultTypeAlias>
  protected _outputTransform: (output: DefaultTypeAlias) => TOut | Promise<TOut>
  protected _agentResponseCallback?: (response: DefaultTypeAlias) => void | Promise<void>
  protected _streamingAgentResponseCallback?: (
    response: StreamingChatMessageContent,
    isLast: boolean
  ) => void | Promise<void>

  /**
   * Initialize the orchestration base.
   *
   * @param members - The list of agents to be used
   * @param name - A unique name of the orchestration. If not provided, a unique name will be generated.
   * @param description - The description of the orchestration. If not provided, use a default description.
   * @param inputTransform - A function that transforms the external input message
   * @param outputTransform - A function that transforms the internal output message
   * @param agentResponseCallback - A function that is called when a full response is produced by the agents
   * @param streamingAgentResponseCallback - A function that is called when a streaming response is produced by the agents
   */
  constructor(options: {
    members: Agent[]
    name?: string
    description?: string
    inputTransform?: (input: TIn) => DefaultTypeAlias | Promise<DefaultTypeAlias>
    outputTransform?: (output: DefaultTypeAlias) => TOut | Promise<TOut>
    agentResponseCallback?: (response: DefaultTypeAlias) => void | Promise<void>
    streamingAgentResponseCallback?: (response: StreamingChatMessageContent, isLast: boolean) => void | Promise<void>
  }) {
    if (!options.members || options.members.length === 0) {
      throw new Error('The members list cannot be empty.')
    }

    this._members = options.members
    this.name = options.name ?? `${this.constructor.name}_${randomUUID()}`
    this.description = options.description ?? 'A multi-agent orchestration.'

    this._inputTransform = options.inputTransform ?? this._defaultInputTransform.bind(this)
    this._outputTransform = options.outputTransform ?? this._defaultOutputTransform.bind(this)
    this._agentResponseCallback = options.agentResponseCallback
    this._streamingAgentResponseCallback = options.streamingAgentResponseCallback
  }

  /**
   * Invoke the multi-agent orchestration.
   * This method is non-blocking and will return immediately.
   * To wait for the result, use the `get` method of the `OrchestrationResult` object.
   *
   * @param task - The task to be executed by the agents
   * @param runtime - The runtime environment for the agents
   * @returns An OrchestrationResult that can be used to get the result
   */
  async invoke(task: string | DefaultTypeAlias | TIn, runtime: CoreRuntime): Promise<OrchestrationResult<TOut>> {
    const orchestrationResult = new OrchestrationResult<TOut>()

    const resultCallback = async (result: DefaultTypeAlias): Promise<void> => {
      try {
        const transformedResult = await this._outputTransform(result)
        orchestrationResult._setResult(transformedResult)
      } catch (error) {
        orchestrationResult._setException(error as Error)
      }
    }

    const innerExceptionCallback = (exception: Error): void => {
      orchestrationResult._setException(exception)
    }

    // This unique topic type is used to isolate the orchestration run from others
    const internalTopicType = randomUUID()

    await this._prepare(runtime, {
      internalTopicType,
      resultCallback,
      exceptionCallback: innerExceptionCallback,
    })

    let preparedTask: DefaultTypeAlias

    if (typeof task === 'string') {
      preparedTask = new ChatMessageContent({
        role: AuthorRole.USER,
        content: task,
      })
    } else if (
      task instanceof ChatMessageContent ||
      (Array.isArray(task) && task.every((item) => item instanceof ChatMessageContent))
    ) {
      preparedTask = task as DefaultTypeAlias
    } else {
      preparedTask = await this._inputTransform(task as TIn)
    }

    const backgroundTask = this._start(
      preparedTask,
      runtime,
      internalTopicType,
      orchestrationResult.cancellationToken
    ).catch((error) => {
      orchestrationResult._setException(error)
    })

    orchestrationResult.backgroundTask = backgroundTask

    return orchestrationResult
  }

  /**
   * Start the multi-agent orchestration.
   *
   * @param task - The task to be executed by the agents
   * @param runtime - The runtime environment for the agents
   * @param internalTopicType - The internal topic type for the orchestration that this actor is part of
   * @param cancellationToken - The cancellation token for the orchestration
   */
  protected abstract _start(
    task: DefaultTypeAlias,
    runtime: CoreRuntime,
    internalTopicType: string,
    cancellationToken: CancellationToken
  ): Promise<void>

  /**
   * Register the actors and orchestrations with the runtime and add the required subscriptions.
   *
   * @param runtime - The runtime environment for the agents
   * @param options - Options for preparation
   */
  protected abstract _prepare(
    runtime: CoreRuntime,
    options: {
      internalTopicType: string
      exceptionCallback: (exception: Error) => void
      resultCallback: (result: DefaultTypeAlias) => Promise<void>
    }
  ): Promise<void>

  /**
   * Default input transform function.
   * This function transforms the external input message to chat message content(s).
   * If the input message is already in the correct format, it is returned as is.
   *
   * @param inputMessage - The input message to be transformed
   * @returns The transformed input message
   */
  protected _defaultInputTransform(inputMessage: TIn): DefaultTypeAlias {
    if (inputMessage instanceof ChatMessageContent) {
      return inputMessage
    }

    if (Array.isArray(inputMessage) && inputMessage.every((item) => item instanceof ChatMessageContent)) {
      return inputMessage as DefaultTypeAlias
    }

    // For plain objects, serialize to JSON
    if (typeof inputMessage === 'object' && inputMessage !== null) {
      return new ChatMessageContent({
        role: AuthorRole.USER,
        content: JSON.stringify(inputMessage),
      })
    }

    throw new TypeError(
      `Invalid input message type: ${typeof inputMessage}. Expected ChatMessageContent or ChatMessageContent[].`
    )
  }

  /**
   * Default output transform function.
   * This function transforms the internal output message to the external output message.
   * If the output message is already in the correct format, it is returned as is.
   *
   * @param outputMessage - The output message to be transformed
   * @returns The transformed output message
   */
  protected _defaultOutputTransform(outputMessage: DefaultTypeAlias): TOut {
    // If TOut is the same as DefaultTypeAlias, return as is
    if (
      outputMessage instanceof ChatMessageContent ||
      (Array.isArray(outputMessage) && outputMessage.every((item) => item instanceof ChatMessageContent))
    ) {
      return outputMessage as unknown as TOut
    }

    // For other types, try to parse from JSON if it's a single ChatMessageContent
    if (outputMessage instanceof ChatMessageContent && outputMessage.content) {
      try {
        return JSON.parse(outputMessage.content) as TOut
      } catch {
        // If JSON parsing fails, return the content as is
        return outputMessage as unknown as TOut
      }
    }

    throw new TypeError(`Unable to transform output message of type ${typeof outputMessage} to the expected type.`)
  }
}
