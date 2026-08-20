import { AgentId } from './agent-id'
import { TopicId } from './topic'

/**
 * Subscriptions define the topics that an agent is interested in.
 *
 * Note: This interface is marked as 'experimental' and may change in the future.
 */
export interface Subscription {
  /**
   * Get the ID of the subscription.
   *
   * Implementations should return a unique ID for the subscription. Usually this is a UUID.
   */
  readonly id: string

  /**
   * Check if two subscriptions are equal.
   *
   * @param other - Other subscription to compare against.
   * @returns True if the subscriptions are equal, false otherwise.
   */
  equals(other: Subscription): boolean

  /**
   * Check if a given topic_id matches the subscription.
   *
   * @param topicId - TopicId to check.
   * @returns True if the topic_id matches the subscription, false otherwise.
   */
  isMatch(topicId: TopicId): boolean

  /**
   * Map a topic_id to an agent. Should only be called if `isMatch` returns true for the given topic_id.
   *
   * @param topicId - TopicId to map.
   * @returns ID of the agent that should handle the topic_id.
   * @throws {Error} If the subscription cannot handle the topic_id.
   */
  mapToAgent(topicId: TopicId): AgentId
}

/**
 * Helper type to represent the functions used to define subscriptions.
 */
export type UnboundSubscription = () => Subscription[] | Promise<Subscription[]>
