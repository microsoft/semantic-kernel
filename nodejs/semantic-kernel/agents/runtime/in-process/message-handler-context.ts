import { AsyncLocalStorage } from 'async_hooks'
import { experimental } from '../../../utils/feature-stage-decorator'
import type { AgentId } from '../core/agent-id'

/**
 * Context for message handlers using AsyncLocalStorage to track the current agent handling a message.
 */
@experimental
export class MessageHandlerContext {
  private static _storage = new AsyncLocalStorage<AgentId>()

  /**
   * MessageHandlerContext cannot be instantiated. It is a static class that provides
   * context management for message handling.
   */
  private constructor() {
    throw new Error(
      'MessageHandlerContext cannot be instantiated. It is a static class that provides context management for message handling.'
    )
  }

  /**
   * Populate the context with the current agent ID and execute the callback within that context.
   * @param agentId - The agent ID to set in the context
   * @param callback - The callback to execute within the context
   * @returns The result of the callback
   */
  static populateContext<T>(agentId: AgentId, callback: () => T | Promise<T>): T | Promise<T> {
    return this._storage.run(agentId, callback)
  }

  /**
   * Get the current agent ID from the context.
   * @returns The current agent ID
   * @throws Error if called outside of a message handler context
   */
  static agentId(): AgentId {
    const agentId = this._storage.getStore()
    if (!agentId) {
      throw new Error('MessageHandlerContext.agentId() must be called within a message handler.')
    }
    return agentId
  }
}
