import { experimental } from '../../../utils/feature-stage-decorator'
import { createDefaultLogger, Logger } from '../../../utils/logger'
import { Agent } from './agent'
import { AgentId } from './agent-id'
import { AgentMetadata, CoreAgentMetadata } from './agent-metadata'
import { AgentType, CoreAgentType } from './agent-type'
import { CancellationToken } from './cancellation-token'
import { MessageContext } from './message-context'
import { TopicId } from './topic'

const logger: Logger = createDefaultLogger('BaseAgent')

/**
 * Interface for core runtime functionality needed by BaseAgent.
 * This is a minimal interface to avoid circular dependencies.
 */
export interface CoreRuntime {
  sendMessage(
    message: any,
    recipient: AgentId,
    options?: {
      sender?: AgentId
      cancellationToken?: CancellationToken
      messageId?: string
    }
  ): Promise<any>

  publishMessage(
    message: any,
    topicId: TopicId,
    options?: {
      sender?: AgentId
      cancellationToken?: CancellationToken
      messageId?: string
    }
  ): Promise<void>

  registerFactory<T extends Agent>(
    type: AgentType | string,
    agentFactory: () => T | Promise<T>,
    options?: {
      expectedClass?: new (...args: any[]) => T
    }
  ): Promise<AgentType>

  addSubscription(subscription: Subscription): Promise<void>

  addMessageSerializer(serializer: MessageSerializer<any> | MessageSerializer<any>[]): void
}

/**
 * Interface for subscriptions that define topics an agent is interested in.
 */
export interface Subscription {
  /**
   * Get the ID of the subscription.
   */
  readonly id: string

  /**
   * Check if a given topic_id matches the subscription.
   */
  isMatch(topicId: TopicId): boolean

  /**
   * Map a topic_id to an agent.
   */
  mapToAgent(topicId: TopicId): AgentId
}

/**
 * Helper type to represent the functions used to define subscriptions.
 */
export type UnboundSubscription = () => Subscription[] | Promise<Subscription[]>

/**
 * Interface for message serializers.
 */
export interface MessageSerializer<T> {
  /**
   * Content type of the data being serialized.
   */
  readonly dataContentType: string

  /**
   * Type name of the message being serialized.
   */
  readonly typeName: string

  /**
   * Deserialize the payload into a message.
   */
  deserialize(payload: Uint8Array): T

  /**
   * Serialize the message into a payload.
   */
  serialize(message: T): Uint8Array
}

/**
 * Context for agent instantiation.
 */
class AgentInstantiationContext {
  private static runtimeStack: CoreRuntime[] = []
  private static agentIdStack: AgentId[] = []

  static currentRuntime(): CoreRuntime {
    if (this.runtimeStack.length === 0) {
      throw new Error(
        'AgentInstantiationContext.currentRuntime() must be called within an instantiation context such as when the ' +
          'AgentRuntime is instantiating an agent. Most likely this was caused by directly instantiating an ' +
          'agent instead of using the AgentRuntime to do so.'
      )
    }
    return this.runtimeStack[this.runtimeStack.length - 1]
  }

  static currentAgentId(): AgentId {
    if (this.agentIdStack.length === 0) {
      throw new Error(
        'AgentInstantiationContext.currentAgentId() must be called within an instantiation context such as when the ' +
          'AgentRuntime is instantiating an agent. Most likely this was caused by directly instantiating an ' +
          'agent instead of using the AgentRuntime to do so.'
      )
    }
    return this.agentIdStack[this.agentIdStack.length - 1]
  }

  static pushContext(runtime: CoreRuntime, agentId: AgentId): void {
    this.runtimeStack.push(runtime)
    this.agentIdStack.push(agentId)
  }

  static popContext(): void {
    this.runtimeStack.pop()
    this.agentIdStack.pop()
  }

  /**
   * Populate the context with runtime and agent ID, execute a function, then clean up.
   * This is the recommended way to use AgentInstantiationContext.
   */
  static populateContext<T>(runtime: CoreRuntime, agentId: AgentId, fn: () => T | Promise<T>): T | Promise<T> {
    this.pushContext(runtime, agentId)
    try {
      const result = fn()
      if (result instanceof Promise) {
        return result.finally(() => this.popContext())
      }
      this.popContext()
      return result
    } catch (error) {
      this.popContext()
      throw error
    }
  }
}

/**
 * Context for subscription instantiation.
 */
class SubscriptionInstantiationContext {
  private static agentTypeStack: AgentType[] = []

  static currentAgentType(): AgentType {
    if (this.agentTypeStack.length === 0) {
      throw new Error('No agent type in context')
    }
    return this.agentTypeStack[this.agentTypeStack.length - 1]
  }

  static pushContext(agentType: AgentType): void {
    this.agentTypeStack.push(agentType)
  }

  static popContext(): void {
    this.agentTypeStack.pop()
  }

  static populateContext<T>(agentType: AgentType, fn: () => T): T {
    this.pushContext(agentType)
    try {
      return fn()
    } finally {
      this.popContext()
    }
  }
}

/**
 * Decorator for adding an unbound subscription to an agent.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function subscriptionFactory(subscription: UnboundSubscription): <T extends typeof BaseAgent>(target: T) => T {
  return function <T extends typeof BaseAgent>(target: T): T {
    target.internalUnboundSubscriptionsList.push(subscription)
    return target
  }
}

/**
 * Decorator for associating a message type and corresponding serializer(s) with a BaseAgent or its subclass.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function handles<MsgType>(
  msgType: new (...args: any[]) => MsgType,
  serializer?: MessageSerializer<MsgType> | MessageSerializer<MsgType>[]
): <T extends typeof BaseAgent>(target: T) => T {
  return function <T extends typeof BaseAgent>(target: T): T {
    let serializerList: MessageSerializer<MsgType>[]

    if (serializer === undefined) {
      // In TypeScript, we can't automatically find serializers like Python can
      // So we require explicit serializers
      throw new Error(`No serializers provided for type ${msgType.name}. Please provide an explicit serializer.`)
    } else {
      serializerList = Array.isArray(serializer) ? serializer : [serializer]
    }

    target.internalExtraHandlesTypes.push([msgType, serializerList])
    return target
  }
}

/**
 * Base class for all agents.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export abstract class BaseAgent implements Agent {
  static internalUnboundSubscriptionsList: UnboundSubscription[] = []
  static internalExtraHandlesTypes: Array<[new (...args: any[]) => any, MessageSerializer<any>[]]> = []

  protected _runtime: CoreRuntime
  protected _id: AgentId
  protected _description: string

  /**
   * Initialize the class when subclassed.
   */
  static {
    // This ensures each subclass gets its own arrays
    const originalExtends = Object.setPrototypeOf
    Object.setPrototypeOf = function (target: any, proto: any) {
      const result = originalExtends.call(Object, target, proto)
      if (proto === BaseAgent || proto?.prototype instanceof BaseAgent) {
        target.internalExtraHandlesTypes = []
        target.internalUnboundSubscriptionsList = []
      }
      return result
    }
  }

  protected static _handlesTypes(): Array<[new (...args: any[]) => any, MessageSerializer<any>[]]> {
    return this.internalExtraHandlesTypes
  }

  protected static _unboundSubscriptions(): UnboundSubscription[] {
    return this.internalUnboundSubscriptionsList
  }

  get metadata(): AgentMetadata {
    if (!this._id) {
      throw new Error('Agent ID is not set')
    }
    return new CoreAgentMetadata(this._id.type, this._id.key, this._description)
  }

  constructor(description: string) {
    try {
      this._runtime = AgentInstantiationContext.currentRuntime()
      this._id = AgentInstantiationContext.currentAgentId()
    } catch (error) {
      throw new Error(
        'BaseAgent must be instantiated within the context of an AgentRuntime. It cannot be directly instantiated.',
        { cause: error }
      )
    }

    if (typeof description !== 'string') {
      throw new Error('Agent description must be a string')
    }
    this._description = description
  }

  get type(): string {
    return this.id.type
  }

  get id(): AgentId {
    return this._id
  }

  get runtime(): CoreRuntime {
    return this._runtime
  }

  /**
   * Handle a message sent to this agent.
   * This is final and should not be overridden.
   */
  async onMessage(message: any, ctx: MessageContext): Promise<any> {
    return await this.onMessageImpl(message, ctx)
  }

  /**
   * Handle a message sent to this agent.
   * Subclasses should implement this method.
   */
  protected abstract onMessageImpl(message: any, ctx: MessageContext): Promise<any>

  /**
   * Send a message to another agent.
   */
  async sendMessage(
    message: any,
    recipient: AgentId,
    options?: {
      cancellationToken?: CancellationToken
      messageId?: string
    }
  ): Promise<any> {
    const cancellationToken = options?.cancellationToken ?? new CancellationToken()

    return await this._runtime.sendMessage(message, recipient, {
      sender: this.id,
      cancellationToken,
      messageId: options?.messageId,
    })
  }

  /**
   * Publish a message to a topic.
   */
  async publishMessage(
    message: any,
    topicId: TopicId,
    options?: {
      cancellationToken?: CancellationToken
    }
  ): Promise<void> {
    await this._runtime.publishMessage(message, topicId, {
      sender: this.id,
      cancellationToken: options?.cancellationToken,
    })
  }

  /**
   * Save the state of the agent.
   */
  async saveState(): Promise<Record<string, any>> {
    logger.warn('saveState not implemented')
    return {}
  }

  /**
   * Load the state of the agent.
   */
  async loadState(_state: Record<string, any>): Promise<void> {
    logger.warn('loadState not implemented')
  }

  /**
   * Close the agent.
   */
  async close(): Promise<void> {
    // Default implementation does nothing
  }

  /**
   * Register the agent with the runtime.
   */
  static async register<T extends BaseAgent>(
    this: new (...args: any[]) => T,
    runtime: CoreRuntime,
    type: string,
    factory: () => T | Promise<T>,
    options?: {
      skipClassSubscriptions?: boolean
      skipDirectMessageSubscription?: boolean
    }
  ): Promise<AgentType> {
    const agentType = new CoreAgentType(type)
    const registeredType = await runtime.registerFactory(agentType, factory, {
      expectedClass: this as any,
    })

    if (!options?.skipClassSubscriptions) {
      const subscriptions: Subscription[] = []

      SubscriptionInstantiationContext.populateContext(registeredType, () => {
        for (const unboundSubscription of (this as any)._unboundSubscriptions()) {
          const subscriptionsListResult = unboundSubscription()

          if (subscriptionsListResult instanceof Promise) {
            subscriptionsListResult.then((subsList) => {
              subscriptions.push(...subsList)
            })
          } else {
            subscriptions.push(...subscriptionsListResult)
          }
        }
      })

      // Wait for any async subscriptions to resolve
      await Promise.resolve()

      for (const subscription of subscriptions) {
        await runtime.addSubscription(subscription)
      }
    }

    if (!options?.skipDirectMessageSubscription) {
      // Would need TypePrefixSubscription implementation
      // This is commented out as it requires additional types
      // await runtime.addSubscription(
      //   new TypePrefixSubscription(
      //     registeredType.type + ":",
      //     registeredType.type
      //   )
      // );
    }

    // Add message serializers
    for (const [_messageType, serializers] of (this as any)._handlesTypes()) {
      runtime.addMessageSerializer(serializers)
    }

    return registeredType
  }
}

// Export the context classes for advanced usage
export { AgentInstantiationContext, SubscriptionInstantiationContext }
