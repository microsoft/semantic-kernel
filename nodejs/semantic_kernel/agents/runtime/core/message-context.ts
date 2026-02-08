import { experimental } from '../../../utils/feature-stage-decorator'
import { AgentId } from './agent-id'
import { CancellationToken } from './cancellation-token'
import { TopicId } from './topic'

/**
 * Context for a message sent to an agent.
 *
 * Note: This class is marked as 'experimental' and may change in the future.
 */
@experimental
export class MessageContext {
  /**
   * The sender of the message.
   */
  sender: AgentId | null

  /**
   * The topic ID of the message.
   */
  topicId: TopicId | null

  /**
   * Whether the message is an RPC call.
   */
  isRpc: boolean

  /**
   * The cancellation token for the message.
   */
  cancellationToken: CancellationToken

  /**
   * The message ID.
   */
  messageId: string

  constructor(options: {
    sender?: AgentId | null
    topicId?: TopicId | null
    isRpc?: boolean
    cancellationToken: CancellationToken
    messageId: string
  }) {
    this.sender = options.sender ?? null
    this.topicId = options.topicId ?? null
    this.isRpc = options.isRpc ?? false
    this.cancellationToken = options.cancellationToken
    this.messageId = options.messageId
  }
}
