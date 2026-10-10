import { experimental } from '../../../utils/feature-stage-decorator'
import { AgentType } from './agent-type'
import { isValidAgentType } from './validation-utils'

/**
 * Defines the minimal interface an AgentId.
 *
 * It must fulfill a 'type' and a 'key' that identify the agent instance.
 *
 * Note: This interface is marked as 'experimental' and may change in the future.
 */
export interface AgentId {
  /**
   * Defines the 'type' or category of the agent.
   */
  readonly type: string

  /**
   * Defines the unique instance key within the agent type.
   */
  readonly key: string

  /**
   * Equality check must differentiate between different IDs.
   */
  equals(other: AgentId): boolean

  /**
   * String representation of the AgentId, e.g. 'type/key'.
   */
  toString(): string
}

/**
 * Core implementation of the AgentId interface.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export class CoreAgentId implements AgentId {
  private readonly _type: string
  private readonly _key: string

  constructor(type: string | AgentType, key: string) {
    // If `type` is itself an AgentType, extract the string property.
    if (typeof type === 'object' && 'type' in type) {
      type = type.type
    }

    if (!isValidAgentType(type)) {
      throw new Error(`Invalid agent type: ${type}. Allowed values MUST match the regex: ^[\\w\\-\\.]+$`)
    }

    this._type = type
    this._key = key
  }

  /**
   * Convert a string of the format `type/key` into a CoreAgentId.
   */
  static fromString(agentId: string): CoreAgentId {
    const items = agentId.split('/', 2)
    if (items.length !== 2) {
      throw new Error(`Invalid agent id: ${agentId}`)
    }
    const [type, key] = items
    return new CoreAgentId(type, key)
  }

  /**
   * The agent's 'type' (or category). Must match `^[\\w\\-\\.]+$`.
   */
  get type(): string {
    return this._type
  }

  /**
   * The agent's instance key, e.g. 'default' or a unique identifier.
   */
  get key(): string {
    return this._key
  }

  /**
   * Check if two AgentIds are equal by comparing 'type' and 'key'.
   */
  equals(other: AgentId): boolean {
    return this.type === other.type && this.key === other.key
  }

  /**
   * Convert the AgentId to a user-friendly string.
   */
  toString(): string {
    return `${this._type}/${this._key}`
  }
}
