import { randomUUID } from 'crypto'
import { experimental } from '../../../utils/feature-stage-decorator'
import { AgentId, CoreAgentId } from '../core/agent-id'
import { AgentType } from '../core/agent-type'
import { CantHandleException } from '../core/routed-agent'
import { Subscription } from '../core/subscription'
import { TopicId } from '../core/topic'

/**
 * This subscription matches on topics based on the type and maps to agents.
 *
 * It uses the source of the topic as the agent key. This subscription causes each source to have
 * its own agent instance.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export class TypeSubscription implements Subscription {
  private readonly _id: string
  private readonly _topicType: string
  private readonly _agentType: string

  /**
   * Initialize the TypeSubscription.
   *
   * @param topicType - Topic type to match against
   * @param agentType - Agent type to handle this subscription
   * @param id - Id of the subscription. If not provided, a new id will be generated.
   */
  constructor(topicType: string, agentType: string | AgentType, id?: string) {
    this._topicType = topicType

    if (typeof agentType === 'object' && 'type' in agentType) {
      this._agentType = agentType.type
    } else {
      this._agentType = agentType
    }

    this._id = id ?? randomUUID()
  }

  /**
   * Get the id of the subscription.
   */
  get id(): string {
    return this._id
  }

  /**
   * Get the topic type of the subscription.
   */
  get topicType(): string {
    return this._topicType
  }

  /**
   * Get the agent type of the subscription.
   */
  get agentType(): string {
    return this._agentType
  }

  /**
   * Check if the topic_id matches the subscription.
   */
  isMatch(topicId: TopicId): boolean {
    return topicId.type === this._topicType
  }

  /**
   * Map the topic_id to an agent_id.
   *
   * @throws {CantHandleException} If the TopicId does not match the subscription
   */
  mapToAgent(topicId: TopicId): AgentId {
    if (!this.isMatch(topicId)) {
      throw new CantHandleException('TopicId does not match the subscription')
    }

    return new CoreAgentId(this._agentType, topicId.source)
  }

  /**
   * Check if two subscriptions are equal.
   */
  equals(other: Subscription): boolean {
    if (!(other instanceof TypeSubscription)) {
      return false
    }

    return this.id === other.id || (this.agentType === other.agentType && this.topicType === other.topicType)
  }
}
