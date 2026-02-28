import { AgentId } from './agent-id'
import { AgentMetadata } from './agent-metadata'
import { MessageContext } from './message-context'

/**
 * Interface for an agent in the runtime system.
 *
 * Note: This interface is marked as 'experimental' and may change in the future.
 */
export interface Agent {
  /**
   * Metadata of the agent.
   */
  readonly metadata: AgentMetadata

  /**
   * ID of the agent.
   */
  readonly id: AgentId

  /**
   * Message handler for the agent. This should only be called by the runtime, not by other agents.
   *
   * @param message - Received message. Type is one of the types in `subscriptions`.
   * @param ctx - Context of the message.
   * @returns Response to the message. Can be null or undefined.
   * @throws {Error} If the message was cancelled.
   * @throws {CantHandleException} If the agent cannot handle the message.
   */
  onMessage(message: any, ctx: MessageContext): Promise<any>

  /**
   * Save the state of the agent. The result must be JSON serializable.
   *
   * @returns The state of the agent as a JSON-serializable object.
   */
  saveState(): Promise<Record<string, any>>

  /**
   * Load in the state of the agent obtained from `saveState`.
   *
   * @param state - State of the agent. Must be JSON serializable.
   */
  loadState(state: Record<string, any>): Promise<void>

  /**
   * Called when the runtime is closed.
   */
  close(): Promise<void>
}
