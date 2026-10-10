import { experimental } from '../../../utils/feature-stage-decorator'

/**
 * Provides a description for an agent: type, key, and an optional 'description' field.
 *
 * Note: This interface is marked as 'experimental' and may change in the future.
 */
export interface AgentMetadata {
  /**
   * Defines the 'type' or category of the agent.
   */
  readonly type: string

  /**
   * Defines the 'key' or identifier of the agent.
   */
  readonly key: string

  /**
   * Defines the 'description' of the agent.
   */
  readonly description: string
}

/**
 * Concrete immutable implementation of AgentMetadata.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export class CoreAgentMetadata implements AgentMetadata {
  private readonly _type: string
  private readonly _key: string
  private readonly _description: string

  constructor(type: string, key: string, description: string = '') {
    this._type = type
    this._key = key
    this._description = description
  }

  get type(): string {
    return this._type
  }

  get key(): string {
    return this._key
  }

  get description(): string {
    return this._description
  }
}
