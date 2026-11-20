import type { TracerProvider } from '@opentelemetry/api'
import { randomUUID } from 'crypto'
import { experimental } from '../../../utils/feature-stage-decorator'
import { createDefaultLogger } from '../../../utils/logger'
import { Agent } from '../core/agent'
import type { AgentId } from '../core/agent-id'
import { CoreAgentId } from '../core/agent-id'
import { AgentMetadata } from '../core/agent-metadata'
import { AgentType, CoreAgentType } from '../core/agent-type'
import { AgentInstantiationContext } from '../core/base-agent'
import { CancellationToken } from '../core/cancellation-token'
import { CoreRuntime } from '../core/core-runtime'
import { MessageDroppedException } from '../core/exceptions'
import { DropMessage, InterventionHandler } from '../core/intervention'
import { MessageContext } from '../core/message-context'
import { JSON_DATA_CONTENT_TYPE, MessageSerializer, SerializationRegistry } from '../core/serialization'
import { Subscription } from '../core/subscription'
import {
  EnvelopeMetadata,
  getTelemetryEnvelopeMetadata,
  MessageRuntimeTracingConfig,
  TraceHelper,
} from '../core/telemetry'
import { TopicId } from '../core/topic'
import { MessageHandlerContext } from './message-handler-context'

const logger = createDefaultLogger('InProcessRuntime')

/**
 * Utility function to check if the intervention handler returned undefined and issue a warning.
 *
 * @param value - The return value to check
 * @param handlerName - Name of the intervention handler method for the warning message
 */
function warnIfUndefined(value: any, handlerName: string): void {
  if (value === undefined) {
    logger.warn(
      `Intervention handler ${handlerName} returned undefined. This might be unintentional. ` +
        'Consider returning the original message or DropMessage explicitly.'
    )
  }
}

/**
 * Message kind enum for event logging.
 */
enum MessageKind {
  DIRECT = 'DIRECT',
  PUBLISH = 'PUBLISH',
  RESPOND = 'RESPOND',
}

/**
 * Delivery stage enum for event logging.
 */
enum DeliveryStage {
  SEND = 'SEND',
  DELIVER = 'DELIVER',
}

/**
 * Helper to create a structured message event for logging.
 */
function logMessageEvent(options: {
  payload: string
  sender: AgentId | null
  receiver: AgentId | TopicId | null
  kind: MessageKind
  deliveryStage: DeliveryStage
}): void {
  logger.info(
    JSON.stringify({
      type: 'Message',
      payload: options.payload,
      sender: options.sender ? options.sender.toString() : null,
      receiver: options.receiver ? options.receiver.toString() : null,
      kind: options.kind,
      delivery_stage: options.deliveryStage,
    })
  )
}

/**
 * Helper to create a structured message dropped event for logging.
 */
function logMessageDroppedEvent(options: {
  payload: string
  sender: AgentId | null
  receiver: AgentId | TopicId | null
  kind: MessageKind
}): void {
  logger.info(
    JSON.stringify({
      type: 'MessageDropped',
      payload: options.payload,
      sender: options.sender ? options.sender.toString() : null,
      receiver: options.receiver ? options.receiver.toString() : null,
      kind: options.kind,
    })
  )
}

/**
 * Helper to create a structured message handler exception event for logging.
 */
function logMessageHandlerExceptionEvent(options: { payload: string; handlingAgent: AgentId; exception: Error }): void {
  logger.info(
    JSON.stringify({
      type: 'MessageHandlerException',
      payload: options.payload,
      handling_agent: options.handlingAgent.toString(),
      exception: options.exception.toString(),
      exception_message: options.exception.message,
      exception_stack: options.exception.stack,
    })
  )
}

/**
 * Helper to create a structured agent construction exception event for logging.
 */
function logAgentConstructionExceptionEvent(options: { agentId: AgentId; exception: Error }): void {
  logger.info(
    JSON.stringify({
      type: 'AgentConstructionException',
      agent_id: options.agentId.toString(),
      exception: options.exception.toString(),
      exception_message: options.exception.message,
      exception_stack: options.exception.stack,
    })
  )
}

/**
 * A message envelope for publishing messages to all agents.
 */
@experimental
class PublishMessageEnvelope {
  message: any
  cancellationToken: CancellationToken
  sender: AgentId | null
  topicId: TopicId
  messageId: string
  metadata: EnvelopeMetadata | null

  constructor(
    message: any,
    cancellationToken: CancellationToken,
    sender: AgentId | null,
    topicId: TopicId,
    messageId: string,
    metadata: EnvelopeMetadata | null = null
  ) {
    this.message = message
    this.cancellationToken = cancellationToken
    this.sender = sender
    this.topicId = topicId
    this.messageId = messageId
    this.metadata = metadata
  }
}

/**
 * A message envelope for sending a message to a specific agent.
 */
@experimental
class SendMessageEnvelope {
  message: any
  sender: AgentId | null
  recipient: AgentId
  cancellationToken: CancellationToken
  messageId: string
  resolve: (value: any) => void
  reject: (reason?: any) => void
  metadata: EnvelopeMetadata | null

  constructor(
    message: any,
    sender: AgentId | null,
    recipient: AgentId,
    cancellationToken: CancellationToken,
    messageId: string,
    resolve: (value: any) => void,
    reject: (reason?: any) => void,
    metadata: EnvelopeMetadata | null = null
  ) {
    this.message = message
    this.sender = sender
    this.recipient = recipient
    this.cancellationToken = cancellationToken
    this.messageId = messageId
    this.resolve = resolve
    this.reject = reject
    this.metadata = metadata
  }
}

/**
 * A message envelope for sending a response to a message.
 */
@experimental
class ResponseMessageEnvelope {
  message: any
  sender: AgentId
  recipient: AgentId | null
  resolve: (value: any) => void
  metadata: EnvelopeMetadata | null
  cancellationToken: CancellationToken

  constructor(
    message: any,
    sender: AgentId,
    recipient: AgentId | null,
    resolve: (value: any) => void,
    metadata: EnvelopeMetadata | null = null,
    cancellationToken: CancellationToken = new CancellationToken()
  ) {
    this.message = message
    this.sender = sender
    this.recipient = recipient
    this.resolve = resolve
    this.metadata = metadata
    this.cancellationToken = cancellationToken
  }
}

type MessageEnvelope = PublishMessageEnvelope | SendMessageEnvelope | ResponseMessageEnvelope

/**
 * A queue implementation with task tracking similar to Python's asyncio.Queue.
 * Supports task_done() and join() for waiting until all enqueued tasks are processed.
 */
class Queue<T> {
  private _queue: T[] = []
  private _unfinishedTasks = 0
  private _finishedEvent: Promise<void> | null = null
  private _finishedResolve: (() => void) | null = null
  private _shutdown = false

  get size(): number {
    return this._queue.length
  }

  async put(item: T): Promise<void> {
    if (this._shutdown) {
      throw new Error('Queue is shut down')
    }
    this._queue.push(item)
    this._unfinishedTasks++
  }

  async get(): Promise<T | undefined> {
    if (this._shutdown && this._queue.length === 0) {
      return undefined
    }
    return this._queue.shift()
  }

  taskDone(): void {
    if (this._unfinishedTasks <= 0) {
      throw new Error('taskDone() called too many times')
    }
    this._unfinishedTasks--
    if (this._unfinishedTasks === 0 && this._finishedResolve) {
      this._finishedResolve()
      this._finishedEvent = null
      this._finishedResolve = null
    }
  }

  async join(): Promise<void> {
    while (this._unfinishedTasks > 0) {
      if (!this._finishedEvent) {
        this._finishedEvent = new Promise((resolve) => {
          this._finishedResolve = resolve
        })
      }
      await this._finishedEvent
    }
  }

  shutdown(immediate: boolean = false): void {
    this._shutdown = true
    if (immediate) {
      this._queue = []
      this._unfinishedTasks = 0
      if (this._finishedResolve) {
        this._finishedResolve()
        this._finishedEvent = null
        this._finishedResolve = null
      }
    }
  }
}

/**
 * Subscription manager to handle topic subscriptions.
 */
class SubscriptionManager {
  private _subscriptions: Subscription[] = []
  private _seenTopics: Set<string> = new Set()
  private _subscribedRecipients: Map<string, AgentId[]> = new Map()

  get subscriptions(): Subscription[] {
    return this._subscriptions
  }

  async addSubscription(subscription: Subscription): Promise<void> {
    // Check if the subscription already exists
    if (this._subscriptions.some((sub) => sub.equals(subscription))) {
      throw new Error('Subscription already exists')
    }

    this._subscriptions.push(subscription)
    this._rebuildSubscriptions(this._seenTopics)
  }

  async removeSubscription(id: string): Promise<void> {
    // Check if the subscription exists
    if (!this._subscriptions.some((sub) => sub.id === id)) {
      throw new Error('Subscription does not exist')
    }

    this._subscriptions = this._subscriptions.filter((sub) => sub.id !== id)

    // Rebuild the subscriptions
    this._rebuildSubscriptions(this._seenTopics)
  }

  async getSubscribedRecipients(topicId: TopicId): Promise<AgentId[]> {
    const topicKey = topicId.toString()
    if (!this._seenTopics.has(topicKey)) {
      this._buildForNewTopic(topicId)
    }
    return this._subscribedRecipients.get(topicKey) || []
  }

  private _rebuildSubscriptions(topics: Set<string>): void {
    this._subscribedRecipients.clear()
    for (const topicKey of topics) {
      const topicId = TopicId.fromString(topicKey)
      this._buildForNewTopic(topicId)
    }
  }

  private _buildForNewTopic(topicId: TopicId): void {
    const topicKey = topicId.toString()
    this._seenTopics.add(topicKey)

    const recipients: AgentId[] = []
    for (const subscription of this._subscriptions) {
      if (subscription.isMatch(topicId)) {
        recipients.push(subscription.mapToAgent(topicId))
      }
    }
    this._subscribedRecipients.set(topicKey, recipients)
  }
}

/**
 * An in-process runtime that processes all messages using a single queue.
 * Messages are delivered in the order they are received.
 */
@experimental
export class InProcessRuntime implements CoreRuntime {
  public _messageQueue: Queue<MessageEnvelope> = new Queue()
  public _shutdown = false
  public _processing = false

  private _agentFactories: Map<string, () => Agent | Promise<Agent>> = new Map()
  private _instantiatedAgents: Map<string, Agent> = new Map()
  private _backgroundTasks: Set<Promise<any>> = new Set()
  private _subscriptionManager = new SubscriptionManager()
  private _runContext: RunContext | null = null
  private _backgroundException: Error | null = null
  private _interventionHandlers: InterventionHandler[] | null = null
  private _serializationRegistry = new SerializationRegistry()
  private _tracerHelper: TraceHelper<any, any, any>
  private _ignoreUnhandledHandlerExceptions: boolean

  constructor(options?: {
    interventionHandlers?: InterventionHandler[]
    tracerProvider?: TracerProvider | null
    ignoreUnhandledExceptions?: boolean
  }) {
    this._interventionHandlers = options?.interventionHandlers || null
    this._ignoreUnhandledHandlerExceptions = options?.ignoreUnhandledExceptions ?? true
    this._tracerHelper = new TraceHelper(
      options?.tracerProvider || null,
      new MessageRuntimeTracingConfig('InProcessRuntime')
    )
  }

  /**
   * Get the number of unprocessed messages in the queue.
   */
  get unprocessedMessagesCount(): number {
    return this._messageQueue.size
  }

  /**
   * Send a message to an agent and get a response.
   */
  async sendMessage(
    message: any,
    recipient: AgentId,
    options?: {
      sender?: AgentId
      cancellationToken?: CancellationToken
      messageId?: string
    }
  ): Promise<any> {
    const cancellationToken = options?.cancellationToken || new CancellationToken()
    const messageId = options?.messageId || randomUUID()
    const sender = options?.sender || null

    const content = (message as any).__dict || message
    logger.info(`Sending message of type ${message.constructor.name} to ${recipient.type}: ${JSON.stringify(content)}`)

    logMessageEvent({
      payload: this._trySerialize(message),
      sender,
      receiver: recipient,
      kind: MessageKind.DIRECT,
      deliveryStage: DeliveryStage.SEND,
    })

    return this._tracerHelper.traceBlock(
      'create',
      recipient,
      null,
      async () => {
        const metadata = getTelemetryEnvelopeMetadata()

        return new Promise((resolve, reject) => {
          if (!this._agentFactories.has(recipient.type)) {
            reject(new Error('Recipient not found'))
            return
          }

          const envelope = new SendMessageEnvelope(
            message,
            sender,
            recipient,
            cancellationToken,
            messageId,
            resolve,
            reject,
            metadata
          )
          this._messageQueue.put(envelope)
        })
      },
      { extraAttributes: { messageType: message.constructor?.name } }
    )
  }

  /**
   * Publish a message to all agents that are subscribed to the topic.
   */
  async publishMessage(
    message: any,
    topicId: TopicId,
    options?: {
      sender?: AgentId
      cancellationToken?: CancellationToken
      messageId?: string
    }
  ): Promise<void> {
    const cancellationToken = options?.cancellationToken || new CancellationToken()
    const messageId = options?.messageId || randomUUID()
    const sender = options?.sender || null

    const content = (message as any).__dict || message
    logger.info(`Publishing message of type ${message.constructor.name} to all subscribers: ${JSON.stringify(content)}`)

    logMessageEvent({
      payload: this._trySerialize(message),
      sender,
      receiver: topicId,
      kind: MessageKind.PUBLISH,
      deliveryStage: DeliveryStage.SEND,
    })

    await this._tracerHelper.traceBlock(
      'create',
      topicId,
      null,
      async () => {
        const metadata = getTelemetryEnvelopeMetadata()
        const envelope = new PublishMessageEnvelope(message, cancellationToken, sender, topicId, messageId, metadata)
        await this._messageQueue.put(envelope)
      },
      { extraAttributes: { messageType: message.constructor?.name } }
    )
  }

  /**
   * Process the next message in the queue.
   */
  async processNext(): Promise<void> {
    await this._processNext()
  }

  async _processNext(): Promise<void> {
    if (this._backgroundException) {
      const e = this._backgroundException
      this._backgroundException = null
      this._shutdown = true
      throw e
    }

    if (this._shutdown) {
      if (this._backgroundException) {
        const e = this._backgroundException
        this._backgroundException = null
        throw e
      }
      return
    }

    const messageEnvelope = await this._messageQueue.get()
    if (!messageEnvelope) {
      // No message to process or queue is shutdown
      if (this._shutdown && this._backgroundException) {
        const e = this._backgroundException
        this._backgroundException = null
        throw e
      }
      await new Promise((resolve) => setTimeout(resolve, 10))
      return
    }

    this._processing = true

    try {
      if (messageEnvelope instanceof SendMessageEnvelope) {
        // Apply intervention handlers for send messages
        let shouldProcess = true
        if (this._interventionHandlers) {
          for (const handler of this._interventionHandlers) {
            await this._tracerHelper.traceBlock(
              'intercept',
              handler.constructor.name,
              messageEnvelope.metadata,
              async () => {
                try {
                  const messageContext = new MessageContext({
                    sender: messageEnvelope.sender || undefined,
                    topicId: undefined,
                    isRpc: true,
                    cancellationToken: messageEnvelope.cancellationToken,
                    messageId: messageEnvelope.messageId,
                  })
                  const tempMessage = await handler.onSend(
                    messageEnvelope.message,
                    messageContext,
                    messageEnvelope.recipient
                  )
                  warnIfUndefined(tempMessage, 'onSend')

                  if (tempMessage === DropMessage) {
                    logger.info(
                      `Message dropped by intervention handler for recipient ${messageEnvelope.recipient.type}`
                    )
                    logMessageDroppedEvent({
                      payload: this._trySerialize(messageEnvelope.message),
                      sender: messageEnvelope.sender,
                      receiver: messageEnvelope.recipient,
                      kind: MessageKind.DIRECT,
                    })
                    messageEnvelope.reject(new MessageDroppedException())
                    this._messageQueue.taskDone()
                    shouldProcess = false
                    return
                  }
                  messageEnvelope.message = tempMessage
                } catch (error) {
                  messageEnvelope.reject(error)
                  this._messageQueue.taskDone()
                  shouldProcess = false
                  return
                }
              }
            )
            if (!shouldProcess) break
          }
        }

        if (shouldProcess) {
          const task = this._processSend(messageEnvelope)
          this._backgroundTasks.add(task)
          task.finally(() => this._backgroundTasks.delete(task))
        }
      } else if (messageEnvelope instanceof PublishMessageEnvelope) {
        // Apply intervention handlers for publish messages
        let shouldProcess = true
        if (this._interventionHandlers) {
          for (const handler of this._interventionHandlers) {
            await this._tracerHelper.traceBlock(
              'intercept',
              handler.constructor.name,
              messageEnvelope.metadata,
              async () => {
                try {
                  const messageContext = new MessageContext({
                    sender: messageEnvelope.sender || undefined,
                    topicId: messageEnvelope.topicId,
                    isRpc: false,
                    cancellationToken: messageEnvelope.cancellationToken,
                    messageId: messageEnvelope.messageId,
                  })
                  const tempMessage = await handler.onPublish(messageEnvelope.message, messageContext)
                  warnIfUndefined(tempMessage, 'onPublish')

                  if (tempMessage === DropMessage) {
                    logger.info(
                      `Published message dropped by intervention handler for topic ${messageEnvelope.topicId.toString()}`
                    )
                    logMessageDroppedEvent({
                      payload: this._trySerialize(messageEnvelope.message),
                      sender: messageEnvelope.sender,
                      receiver: messageEnvelope.topicId,
                      kind: MessageKind.PUBLISH,
                    })
                    this._messageQueue.taskDone()
                    shouldProcess = false
                    return
                  }
                  messageEnvelope.message = tempMessage
                } catch (error) {
                  logger.error('Exception raised in intervention handler:', error)
                  this._messageQueue.taskDone()
                  shouldProcess = false
                  return
                }
              }
            )
            if (!shouldProcess) break
          }
        }

        if (shouldProcess) {
          const task = this._processPublish(messageEnvelope)
          this._backgroundTasks.add(task)
          task.finally(() => this._backgroundTasks.delete(task))
        }
      } else if (messageEnvelope instanceof ResponseMessageEnvelope) {
        // Apply intervention handlers for response messages
        let shouldProcess = true
        if (this._interventionHandlers) {
          for (const handler of this._interventionHandlers) {
            try {
              const tempMessage = await handler.onResponse(
                messageEnvelope.message,
                messageEnvelope.sender,
                messageEnvelope.recipient
              )
              warnIfUndefined(tempMessage, 'onResponse')

              if (tempMessage === DropMessage) {
                logger.info(`Response message dropped by intervention handler from ${messageEnvelope.sender.type}`)
                logMessageDroppedEvent({
                  payload: this._trySerialize(messageEnvelope.message),
                  sender: messageEnvelope.sender,
                  receiver: messageEnvelope.recipient,
                  kind: MessageKind.RESPOND,
                })
                messageEnvelope.resolve(new MessageDroppedException())
                this._messageQueue.taskDone()
                shouldProcess = false
                break
              }
              messageEnvelope.message = tempMessage
            } catch (error) {
              messageEnvelope.resolve(error)
              this._messageQueue.taskDone()
              shouldProcess = false
              break
            }
          }
        }

        // Process response synchronously (not as background task)
        if (shouldProcess) {
          await this._processResponse(messageEnvelope)
        }
      }
    } finally {
      this._processing = false
    }

    // Yield control to allow other tasks to run
    await new Promise((resolve) => setImmediate(resolve))
  }

  private async _processSend(messageEnvelope: SendMessageEnvelope): Promise<void> {
    await this._tracerHelper.traceBlock('send', messageEnvelope.recipient, messageEnvelope.metadata, async () => {
      const recipient = messageEnvelope.recipient

      if (!this._agentFactories.has(recipient.type)) {
        messageEnvelope.reject(new Error(`Agent type '${recipient.type}' does not exist.`))
        return
      }

      try {
        const senderIdStr = messageEnvelope.sender ? messageEnvelope.sender.toString() : 'Unknown'
        logger.info(
          `Calling message handler for ${recipient} with message type ${messageEnvelope.message.constructor.name} sent by ${senderIdStr}`
        )

        logMessageEvent({
          payload: this._trySerialize(messageEnvelope.message),
          sender: messageEnvelope.sender,
          receiver: recipient,
          kind: MessageKind.DIRECT,
          deliveryStage: DeliveryStage.DELIVER,
        })

        const recipientAgent = await this._getAgent(recipient)

        const messageContext = new MessageContext({
          sender: messageEnvelope.sender || undefined,
          topicId: undefined,
          isRpc: true,
          cancellationToken: messageEnvelope.cancellationToken,
          messageId: messageEnvelope.messageId,
        })

        // Wrap message processing with 'process' tracing and MessageHandlerContext
        const response = await this._tracerHelper.traceBlock(
          'process',
          recipientAgent.id,
          messageEnvelope.metadata,
          async () => {
            return MessageHandlerContext.populateContext(recipientAgent.id, async () => {
              return await recipientAgent.onMessage(messageEnvelope.message, messageContext)
            })
          }
        )

        logMessageEvent({
          payload: this._trySerialize(response),
          sender: messageEnvelope.recipient,
          receiver: messageEnvelope.sender,
          kind: MessageKind.RESPOND,
          deliveryStage: DeliveryStage.SEND,
        })

        // Queue the response
        const responseEnvelope = new ResponseMessageEnvelope(
          response,
          messageEnvelope.recipient,
          messageEnvelope.sender,
          messageEnvelope.resolve,
          messageEnvelope.metadata,
          messageEnvelope.cancellationToken
        )
        await this._messageQueue.put(responseEnvelope)
        this._messageQueue.taskDone()
      } catch (error) {
        const err = error as Error

        // Check if this is a cancellation error
        const isCancellationError =
          err.name === 'AbortError' ||
          err.name === 'CancelledError' ||
          err.name === 'CancellationError' ||
          messageEnvelope.cancellationToken.isCancelled()

        if (isCancellationError) {
          // Handle cancellation specifically - only reject if not already settled
          logMessageHandlerExceptionEvent({
            payload: this._trySerialize(messageEnvelope.message),
            handlingAgent: recipient,
            exception: err,
          })
          // In JavaScript, we can't check if a promise is settled, so we always reject
          // The consumer should handle the cancellation appropriately
          messageEnvelope.reject(err)
          this._messageQueue.taskDone()
          return
        }

        // Handle other exceptions
        logMessageHandlerExceptionEvent({
          payload: this._trySerialize(messageEnvelope.message),
          handlingAgent: recipient,
          exception: err,
        })
        messageEnvelope.reject(err)
        this._messageQueue.taskDone()
      }
    })
  }

  private async _processPublish(messageEnvelope: PublishMessageEnvelope): Promise<void> {
    try {
      const recipients = await this._subscriptionManager.getSubscribedRecipients(messageEnvelope.topicId)
      const responses: Promise<any>[] = []

      for (const agentId of recipients) {
        // Avoid sending the message back to the sender
        if (messageEnvelope.sender && agentId.toString() === messageEnvelope.sender.toString()) {
          continue
        }

        const senderName = messageEnvelope.sender ? messageEnvelope.sender.toString() : 'Unknown'
        logger.info(
          `Calling message handler for ${agentId.type} with message type ${messageEnvelope.message.constructor.name} published by ${senderName}`
        )

        logMessageEvent({
          payload: this._trySerialize(messageEnvelope.message),
          sender: messageEnvelope.sender,
          receiver: null,
          kind: MessageKind.PUBLISH,
          deliveryStage: DeliveryStage.DELIVER,
        })

        const messageContext = new MessageContext({
          sender: messageEnvelope.sender || undefined,
          topicId: messageEnvelope.topicId,
          isRpc: false,
          cancellationToken: messageEnvelope.cancellationToken,
          messageId: messageEnvelope.messageId,
        })

        const agent = await this._getAgent(agentId)

        const onMessage = async (): Promise<any> => {
          return this._tracerHelper.traceBlock('process', agent.id, messageEnvelope.metadata, async () => {
            return MessageHandlerContext.populateContext(agent.id, async () => {
              try {
                return await agent.onMessage(messageEnvelope.message, messageContext)
              } catch (error) {
                logger.error(`Error processing publish message for ${agentId}`, error)
                logMessageHandlerExceptionEvent({
                  payload: this._trySerialize(messageEnvelope.message),
                  handlingAgent: agentId,
                  exception: error as Error,
                })
                if (!this._ignoreUnhandledHandlerExceptions) {
                  throw error
                }
                return undefined
              }
            })
          })
        }

        responses.push(onMessage())
      }

      await Promise.all(responses)
    } catch (error) {
      this._backgroundException = error as Error
    } finally {
      this._messageQueue.taskDone()
    }
  }

  private async _processResponse(messageEnvelope: ResponseMessageEnvelope): Promise<void> {
    await this._tracerHelper.traceBlock('ack', messageEnvelope.recipient, messageEnvelope.metadata, async () => {
      const content = (messageEnvelope.message as any).__dict || messageEnvelope.message
      logger.info(
        `Resolving response with message type ${messageEnvelope.message.constructor.name} for recipient ${messageEnvelope.recipient} from ${messageEnvelope.sender.type}: ${JSON.stringify(content)}`
      )

      logMessageEvent({
        payload: this._trySerialize(content),
        sender: messageEnvelope.sender,
        receiver: messageEnvelope.recipient,
        kind: MessageKind.RESPOND,
        deliveryStage: DeliveryStage.DELIVER,
      })

      // Check if the operation was cancelled before resolving
      if (!messageEnvelope.cancellationToken.isCancelled()) {
        messageEnvelope.resolve(messageEnvelope.message)
      }
      this._messageQueue.taskDone()
    })
  }

  /**
   * Start the runtime message processing loop.
   */
  start(): void {
    if (this._runContext) {
      throw new Error('Runtime is already started')
    }
    this._runContext = new RunContext(this)
  }

  /**
   * Close the runtime and all instantiated agents.
   */
  async close(): Promise<void> {
    if (this._runContext) {
      await this.stop()
    }

    // Close all the agents that have been instantiated
    for (const [_, agent] of this._instantiatedAgents) {
      await agent.close()
    }
  }

  /**
   * Immediately stop the runtime message processing loop.
   */
  async stop(): Promise<void> {
    if (!this._runContext) {
      throw new Error('Runtime is not started')
    }

    try {
      await this._runContext.stop()
    } finally {
      this._runContext = null
      this._messageQueue = new Queue()
    }
  }

  /**
   * Stop the runtime when there are no outstanding messages.
   */
  async stopWhenIdle(): Promise<void> {
    if (!this._runContext) {
      throw new Error('Runtime is not started')
    }

    try {
      await this._runContext.stopWhenIdle()
    } finally {
      this._runContext = null
      this._messageQueue = new Queue()
    }
  }

  /**
   * Stop the runtime when the condition is met.
   */
  async stopWhen(condition: () => boolean): Promise<void> {
    if (!this._runContext) {
      throw new Error('Runtime is not started')
    }

    await this._runContext.stopWhen(condition)
    this._runContext = null
    this._messageQueue = new Queue()
  }

  /**
   * Get the metadata for an agent.
   */
  async agentMetadata(agent: AgentId): Promise<AgentMetadata> {
    return (await this._getAgent(agent)).metadata
  }

  /**
   * Save the state of a single agent.
   */
  async agentSaveState(agent: AgentId): Promise<Record<string, any>> {
    return await (await this._getAgent(agent)).saveState()
  }

  /**
   * Load the state of a single agent.
   */
  async agentLoadState(agent: AgentId, state: Record<string, any>): Promise<void> {
    await (await this._getAgent(agent)).loadState(state)
  }

  /**
   * Register a factory for creating agents.
   */
  async registerFactory<T extends Agent>(
    type: string | AgentType,
    agentFactory: () => T | Promise<T>,
    options?: {
      expectedClass?: new (...args: any[]) => T
    }
  ): Promise<AgentType> {
    const agentType = typeof type === 'string' ? new CoreAgentType(type) : type

    if (this._agentFactories.has(agentType.type)) {
      throw new Error(`Agent with type ${agentType} already exists.`)
    }

    const factoryWrapper = async (): Promise<T> => {
      const agentInstance = await agentFactory()

      if (options?.expectedClass && !(agentInstance instanceof options.expectedClass)) {
        throw new Error('Factory registered using the wrong type.')
      }

      return agentInstance
    }

    this._agentFactories.set(agentType.type, factoryWrapper)

    return agentType
  }

  private async _getAgent(agentId: AgentId): Promise<Agent> {
    const key = agentId.toString()

    if (this._instantiatedAgents.has(key)) {
      return this._instantiatedAgents.get(key)!
    }

    if (!this._agentFactories.has(agentId.type)) {
      throw new Error(`Agent with name ${agentId.type} not found.`)
    }

    try {
      const agentFactory = this._agentFactories.get(agentId.type)!
      // Populate the context during agent instantiation so agents can access runtime and ID
      const agent = await AgentInstantiationContext.populateContext(this as any, agentId, () => agentFactory())
      this._instantiatedAgents.set(key, agent)
      return agent
    } catch (error) {
      logAgentConstructionExceptionEvent({
        agentId,
        exception: error as Error,
      })
      logger.error(`Error constructing agent ${agentId}`, error)
      throw error
    }
  }

  /**
   * Try to get the underlying agent instance.
   */
  async tryGetUnderlyingAgentInstance<T extends Agent>(id: AgentId, type?: new (...args: any[]) => T): Promise<T> {
    if (!this._agentFactories.has(id.type)) {
      throw new Error(`Agent with name ${id.type} not found.`)
    }

    const agentInstance = await this._getAgent(id)

    if (type && !(agentInstance instanceof type)) {
      throw new TypeError(
        `Agent with name ${id.type} is not of type ${type.name}. It is of type ${agentInstance.constructor.name}`
      )
    }

    return agentInstance as T
  }

  /**
   * Add a subscription to the runtime.
   */
  async addSubscription(subscription: Subscription): Promise<void> {
    await this._subscriptionManager.addSubscription(subscription)
  }

  /**
   * Remove a subscription from the runtime.
   */
  async removeSubscription(id: string): Promise<void> {
    await this._subscriptionManager.removeSubscription(id)
  }

  /**
   * Get an agent by id or type.
   */
  async get(
    idOrType: AgentId | AgentType | string,
    key: string = 'default',
    options?: { lazy?: boolean }
  ): Promise<AgentId> {
    const lazy = options?.lazy ?? true

    if (typeof idOrType === 'string') {
      const agentId = new CoreAgentId(idOrType, key)
      if (!lazy) {
        await this._getAgent(agentId)
      }
      return agentId
    } else if ('key' in idOrType) {
      // It's an AgentId (has both 'type' and 'key' properties)
      if (!lazy) {
        await this._getAgent(idOrType)
      }
      return idOrType
    } else {
      // It's an AgentType (has only 'type' property)
      const agentId = new CoreAgentId(idOrType.type, key)
      if (!lazy) {
        await this._getAgent(agentId)
      }
      return agentId
    }
  }

  /**
   * Save the state of all instantiated agents.
   */
  async saveState(): Promise<Record<string, any>> {
    const state: Record<string, Record<string, any>> = {}
    for (const [agentIdStr, _] of this._instantiatedAgents) {
      const agentId = CoreAgentId.fromString(agentIdStr)
      state[agentIdStr] = await (await this._getAgent(agentId)).saveState()
    }
    return state
  }

  /**
   * Load the state of all instantiated agents.
   */
  async loadState(state: Record<string, any>): Promise<void> {
    for (const agentIdStr in state) {
      const agentId = CoreAgentId.fromString(agentIdStr)
      if (this._agentFactories.has(agentId.type)) {
        await (await this._getAgent(agentId)).loadState(state[agentIdStr])
      }
    }
  }

  /**
   * Add a message serializer to the runtime.
   */
  addMessageSerializer(serializer: MessageSerializer<any> | MessageSerializer<any>[]): void {
    this._serializationRegistry.addSerializer(serializer)
  }

  /**
   * Try to serialize a message to a string representation.
   * Returns "Message could not be serialized" if serialization fails.
   */
  private _trySerialize(message: any): string {
    try {
      const typeName = this._serializationRegistry.getTypeName(message)
      const payload = this._serializationRegistry.serialize(message, {
        typeName,
        dataContentType: JSON_DATA_CONTENT_TYPE,
      })
      return new TextDecoder().decode(payload)
    } catch (error) {
      logger.warn('Failed to serialize message for logging:', error)
      return 'Message could not be serialized'
    }
  }
}

/**
 * A context for the runtime to run in a background task.
 */
@experimental
class RunContext {
  private _runtime: InProcessRuntime
  private _runPromise: Promise<void> | null = null
  private _stopped = false

  constructor(runtime: InProcessRuntime) {
    this._runtime = runtime
    this._runPromise = this._run()
  }

  private async _run(): Promise<void> {
    while (!this._stopped) {
      await this._runtime._processNext()
    }
  }

  async stop(): Promise<void> {
    this._stopped = true
    this._runtime._shutdown = true
    this._runtime._messageQueue.shutdown(true)
    if (this._runPromise) {
      await this._runPromise
    }
  }

  async stopWhenIdle(): Promise<void> {
    // Wait until all tasks are done
    await this._runtime._messageQueue.join()
    this._stopped = true
    this._runtime._shutdown = true
    this._runtime._messageQueue.shutdown(true)
    if (this._runPromise) {
      await this._runPromise
    }
  }

  async stopWhen(condition: () => boolean, checkPeriod: number = 1000): Promise<void> {
    const checkCondition = async (): Promise<void> => {
      while (!condition()) {
        await new Promise((resolve) => setTimeout(resolve, checkPeriod))
      }
      await this.stop()
    }
    await checkCondition()
  }
}
