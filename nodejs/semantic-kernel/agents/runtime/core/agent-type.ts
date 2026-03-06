import { experimental } from '../../../utils/feature-stage-decorator'

/**
 * Defines the minimal interface an AgentType.
 *
 * Note: This interface is marked as 'experimental' and may change in the future.
 */
export interface AgentType {
  /**
   * Defines the 'type' or category of the agent.
   */
  readonly type: string
}

/**
 * Concrete immutable implementation of AgentType.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export class CoreAgentType implements AgentType {
  private readonly _type: string

  constructor(type: string) {
    this._type = type
  }

  get type(): string {
    return this._type
  }

  toString(): string {
    return this._type
  }
}
