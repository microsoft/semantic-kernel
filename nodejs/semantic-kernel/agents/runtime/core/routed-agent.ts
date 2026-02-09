import { experimental } from '../../../utils/feature-stage-decorator'
import { BaseAgent } from './base-agent'
import { MessageContext } from './message-context'

/**
 * Exception thrown when an agent cannot handle a message.
 */
export class CantHandleException extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'CantHandleException'
  }
}

/**
 * Interface for message handlers.
 */
export interface MessageHandler<TAgent, TReceives, TProduces> {
  /**
   * Types this handler can receive.
   */
  targetTypes: Array<new (...args: any[]) => any>

  /**
   * Types this handler can produce.
   */
  producesTypes: Array<new (...args: any[]) => any>

  /**
   * Indicates this is a message handler.
   */
  isMessageHandler: true

  /**
   * Router function for secondary routing after message type matching.
   */
  router: (message: TReceives, ctx: MessageContext) => boolean;

  /**
   * The handler function.
   */
  (agentInstance: TAgent, message: TReceives, ctx: MessageContext): Promise<TProduces>
}

/**
 * Options for message handler decorators.
 */
export interface MessageHandlerOptions<TReceives> {
  /**
   * If true, the handler will raise an exception if the message type or return type is not in the target types.
   * If false, it will log a warning instead.
   */
  strict?: boolean

  /**
   * A function that takes the message and the context as arguments and returns a boolean.
   * This is used for secondary routing after the message type.
   */
  match?: (message: TReceives, ctx: MessageContext) => boolean
}

/**
 * Decorator for generic message handlers.
 *
 * Add this decorator to methods in a RoutedAgent class that are intended to handle both
 * event and RPC messages.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function messageHandler<TAgent, TReceives, TProduces>(
  options?: MessageHandlerOptions<TReceives>
): (
  target: any,
  propertyKey: string,
  descriptor: TypedPropertyDescriptor<(this: TAgent, message: TReceives, ctx: MessageContext) => Promise<TProduces>>
) => void {
  return function (
    _target: any,
    _propertyKey: string,
    descriptor: TypedPropertyDescriptor<(this: TAgent, message: TReceives, ctx: MessageContext) => Promise<TProduces>>
  ): void {
    const originalMethod = descriptor.value!
    // const strict = options?.strict ?? true
    const match = options?.match

    // We can't extract type hints at runtime in TypeScript like Python
    // So we'll require explicit type registration or use metadata
    const handler = originalMethod as any as MessageHandler<TAgent, TReceives, TProduces>
    handler.targetTypes = handler.targetTypes || []
    handler.producesTypes = handler.producesTypes || []
    handler.isMessageHandler = true
    handler.router = match || ((_message, _ctx) => true)
  }
}

/**
 * Decorator for event message handlers.
 *
 * Add this decorator to methods in a RoutedAgent class that are intended to handle event messages.
 * These methods must return void/Promise<void>.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function event<TAgent, TReceives>(
  options?: MessageHandlerOptions<TReceives>
): (
  _target: any,
  _propertyKey: string,
  descriptor: TypedPropertyDescriptor<(this: TAgent, message: TReceives, ctx: MessageContext) => Promise<void>>
) => void {
  return function (
    _target: any,
    _propertyKey: string,
    descriptor: TypedPropertyDescriptor<(this: TAgent, message: TReceives, ctx: MessageContext) => Promise<void>>
  ): void {
    const originalMethod = descriptor.value!
    const match = options?.match

    const handler = originalMethod as any as MessageHandler<TAgent, TReceives, void>
    handler.targetTypes = handler.targetTypes || []
    handler.producesTypes = []
    handler.isMessageHandler = true
    // Wrap the match function with a check on the is_rpc flag
    handler.router = (_message, _ctx) => !_ctx.isRpc && (match ? match(_message, _ctx) : true)
  }
}

/**
 * Decorator for RPC message handlers.
 *
 * Add this decorator to methods in a RoutedAgent class that are intended to handle RPC messages.
 * These methods must return a response value.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function rpc<TAgent, TReceives, TProduces>(
  options?: MessageHandlerOptions<TReceives>
): (
  _target: any,
  _propertyKey: string,
  descriptor: TypedPropertyDescriptor<(this: TAgent, message: TReceives, ctx: MessageContext) => Promise<TProduces>>
) => void {
  return function (
    _target: any,
    _propertyKey: string,
    descriptor: TypedPropertyDescriptor<(this: TAgent, message: TReceives, ctx: MessageContext) => Promise<TProduces>>
  ): void {
    const originalMethod = descriptor.value!
    const match = options?.match

    const handler = originalMethod as any as MessageHandler<TAgent, TReceives, TProduces>
    handler.targetTypes = handler.targetTypes || []
    handler.producesTypes = handler.producesTypes || []
    handler.isMessageHandler = true
    // Wrap the match function with a check on the is_rpc flag
    handler.router = (_message, _ctx) => _ctx.isRpc && (match ? match(_message, _ctx) : true)
  }
}

/**
 * A base class for agents that route messages to handlers.
 *
 * Messages are routed based on the type of the message and optional matching functions.
 *
 * To create a routed agent, subclass this class and add message handlers as methods decorated with
 * either @event or @rpc decorator.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export abstract class RoutedAgent extends BaseAgent {
  protected _handlers: Map<new (...args: any[]) => any, MessageHandler<RoutedAgent, any, any>[]> = new Map()

  constructor(description: string) {
    super(description)

    // Discover handlers after calling super
    const handlers = (this.constructor as typeof RoutedAgent)._discoverHandlers()
    for (const messageHandler of handlers) {
      for (const targetType of messageHandler.targetTypes) {
        const existing = this._handlers.get(targetType) || []
        existing.push(messageHandler)
        this._handlers.set(targetType, existing)
      }
    }
  }

  /**
   * Handle a message by routing it to the appropriate message handler.
   *
   * Do not override this method in subclasses. Instead, add message handlers as methods decorated with
   * either the @event or @rpc decorator.
   */
  protected async onMessageImpl(message: any, ctx: MessageContext): Promise<any> {
    const keyType = message.constructor
    const handlers = this._handlers.get(keyType)

    if (handlers) {
      // Iterate over all handlers for this matching message type.
      // Call the first handler whose router returns true and then return the result.
      for (const h of handlers) {
        if (h.router(message, ctx)) {
          return await h(this, message, ctx)
        }
      }
    }

    return await this.onUnhandledMessage(message, ctx)
  }

  /**
   * Called when a message is received that does not have a matching message handler.
   *
   * The default implementation logs an info message.
   *
   * @param message - The message that was not handled.
   * @param ctx - The context of the message.
   */
  protected async onUnhandledMessage(message: any, _ctx: MessageContext): Promise<void> {
    console.info(`Unhandled message: ${JSON.stringify(message)}`)
  }

  /**
   * Discover all message handlers in the class.
   */
  protected static _discoverHandlers(): MessageHandler<any, any, any>[] {
    const handlers: MessageHandler<any, any, any>[] = []
    const proto = this.prototype

    // Get all property names from the prototype chain
    const propertyNames = Object.getOwnPropertyNames(proto)

    for (const attr of propertyNames) {
      const descriptor = Object.getOwnPropertyDescriptor(proto, attr)
      if (descriptor && typeof descriptor.value === 'function') {
        const handler = descriptor.value
        if ((handler as any).isMessageHandler) {
          handlers.push(handler as MessageHandler<any, any, any>)
        }
      }
    }

    return handlers
  }

  /**
   * Get the types this agent can handle along with their serializers.
   */
  protected static _handlesTypes(): Array<[new (...args: any[]) => any, any[]]> {
    const handlers = this._discoverHandlers()
    const types: Array<[new (...args: any[]) => any, any[]]> = []

    // Add types from parent class
    types.push(...this.internalExtraHandlesTypes)

    for (const handler of handlers) {
      for (const t of handler.targetTypes) {
        // In TypeScript, we'd need to register serializers explicitly
        // This is a placeholder for the serializer lookup
        types.push([t, []])
      }
    }

    return types
  }
}
