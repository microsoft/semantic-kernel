import { Agent } from './agent'
import { AgentId } from './agent-id'
import { AgentMetadata } from './agent-metadata'
import { AgentType } from './agent-type'
import { CancellationToken } from './cancellation-token'
import { MessageSerializer } from './serialization'
import { Subscription } from './subscription'
import { TopicId } from './topic'

/**
 * CoreRuntime is the main entry point for the agent runtime.
 * It is responsible for managing agents and their interactions.
 */
export interface CoreRuntime {
  /**
   * Send a message to an agent and get a response.
   *
   * @param message - The message to send
   * @param recipient - The agent to send the message to
   * @param options - Additional options
   * @returns The response from the agent
   * @throws {Error} If the recipient cannot handle the message
   * @throws {Error} If the message cannot be delivered
   */
  sendMessage(
    message: any,
    recipient: AgentId,
    options?: {
      sender?: AgentId
      cancellationToken?: CancellationToken
      messageId?: string
    }
  ): Promise<any>

  /**
   * Publish a message to all agents in the given topic.
   * No responses are expected from publishing.
   *
   * @param message - The message to publish
   * @param topicId - The topic to publish the message to
   * @param options - Additional options
   * @throws {Error} If the message cannot be delivered
   */
  publishMessage(
    message: any,
    topicId: TopicId,
    options?: {
      sender?: AgentId
      cancellationToken?: CancellationToken
      messageId?: string
    }
  ): Promise<void>

  /**
   * Register an agent factory with the runtime associated with a specific type.
   * The type must be unique. This API does not add any subscriptions.
   *
   * @param type - The type of agent this factory creates
   * @param agentFactory - The factory that creates the agent
   * @param options - Additional options
   * @returns The registered agent type
   */
  registerFactory<T extends Agent>(
    type: string | AgentType,
    agentFactory: () => T | Promise<T>,
    options?: {
      expectedClass?: new (...args: any[]) => T
    }
  ): Promise<AgentType>

  /**
   * Try to get the underlying agent instance by id.
   * This is generally discouraged (hence the long name), but can be useful in some cases.
   *
   * @param id - The agent id
   * @param type - The expected type of the agent
   * @returns The concrete agent instance
   * @throws {Error} If the agent is not found
   * @throws {Error} If the agent is not accessible (e.g., located remotely)
   * @throws {TypeError} If the agent is not of the expected type
   */
  tryGetUnderlyingAgentInstance<T extends Agent>(id: AgentId, type?: new (...args: any[]) => T): Promise<T>

  /**
   * Get an agent by id or type.
   *
   * @param idOrType - The agent id or type
   * @param key - The key for the agent (when using type)
   * @param options - Additional options
   * @returns The agent id
   */
  get(idOrType: AgentId | AgentType | string, key?: string, options?: { lazy?: boolean }): Promise<AgentId>

  /**
   * Get the metadata for an agent.
   *
   * @param agent - The agent id
   * @returns The agent metadata
   */
  agentMetadata(agent: AgentId): Promise<AgentMetadata>

  /**
   * Save the state of a single agent.
   * The structure of the state is implementation defined and can be any JSON serializable object.
   *
   * @param agent - The agent id
   * @returns The saved state
   */
  agentSaveState(agent: AgentId): Promise<Record<string, any>>

  /**
   * Load the state of a single agent.
   *
   * @param agent - The agent id
   * @param state - The saved state
   */
  agentLoadState(agent: AgentId, state: Record<string, any>): Promise<void>

  /**
   * Add a new subscription that the runtime should fulfill when processing published messages.
   *
   * @param subscription - The subscription to add
   */
  addSubscription(subscription: Subscription): Promise<void>

  /**
   * Remove a subscription from the runtime.
   *
   * @param id - id of the subscription to remove
   * @throws {Error} If the subscription does not exist
   */
  removeSubscription(id: string): Promise<void>

  /**
   * Add a new message serialization serializer to the runtime.
   * Note: This will deduplicate serializers based on the type_name and data_content_type properties.
   *
   * @param serializer - The serializer/s to add
   */
  addMessageSerializer(serializer: MessageSerializer<any> | MessageSerializer<any>[]): void
}
