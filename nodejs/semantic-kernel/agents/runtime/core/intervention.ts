import { experimental } from '../../../utils/feature-stage-decorator'
import { AgentId } from './agent-id'
import { MessageContext } from './message-context'

/**
 * Marker class for signalling that a message should be dropped by an intervention handler.
 *
 * Return the class itself (DropMessage) from the handler to drop a message.
 */
@experimental
export class DropMessage {
  private constructor() {
    // Private constructor to prevent instantiation
  }
}

/**
 * An intervention handler is a class that can be used to modify, log or drop messages.
 *
 * These messages are being processed by the CoreRuntime.
 *
 * The handler is called when the message is submitted to the runtime.
 *
 * Note: Returning undefined from any of the intervention handler methods will result in a warning being issued
 * and treated as "no change". If you intend to drop a message, you should return DropMessage explicitly.
 */
export interface InterventionHandler {
  /**
   * Called when a message is submitted to the AgentRuntime via sendMessage.
   *
   * @param message - The message being sent
   * @param messageContext - Context information about the message
   * @param recipient - The recipient of the message
   * @returns The modified message, or DropMessage to prevent delivery
   */
  onSend(message: any, messageContext: MessageContext, recipient: AgentId): Promise<any | typeof DropMessage>

  /**
   * Called when a message is published to the AgentRuntime via publishMessage.
   *
   * @param message - The message being published
   * @param messageContext - Context information about the message
   * @returns The modified message, or DropMessage to prevent delivery
   */
  onPublish(message: any, messageContext: MessageContext): Promise<any | typeof DropMessage>

  /**
   * Called when a response is received by the AgentRuntime from an Agent's message handler returning a value.
   *
   * @param message - The response message
   * @param sender - The agent that sent the response
   * @param recipient - The recipient of the response (may be null)
   * @returns The modified message, or DropMessage to prevent delivery
   */
  onResponse(message: any, sender: AgentId, recipient: AgentId | null): Promise<any | typeof DropMessage>
}

/**
 * Simple class that provides a default implementation for all intervention handler methods.
 *
 * Simply returns the message unchanged. Allows for easy subclassing to override only the desired methods.
 */
@experimental
export class DefaultInterventionHandler implements InterventionHandler {
  /**
   * Called when a message is submitted to the AgentRuntime.
   */
  async onSend(message: any, _messageContext: MessageContext, _recipient: AgentId): Promise<any | typeof DropMessage> {
    return message
  }

  /**
   * Called when a message is published to the AgentRuntime.
   */
  async onPublish(message: any, _messageContext: MessageContext): Promise<any | typeof DropMessage> {
    return message
  }

  /**
   * Called when a response is received by the AgentRuntime from an Agent's message handler returning a value.
   */
  async onResponse(message: any, _sender: AgentId, _recipient: AgentId | null): Promise<any | typeof DropMessage> {
    return message
  }
}
