import { ChatHistory } from '../../contents/chat-history'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { AuthorRole } from '../../contents/utils/author-role'
import { experimental } from '../../utils/feature-stage-decorator'
import { createDefaultLogger } from '../../utils/logger'
import { Agent } from '../agent'
import { CancellationToken } from '../runtime/core/cancellation-token'
import { CoreRuntime } from '../runtime/core/core-runtime'
import { MessageContext } from '../runtime/core/message-context'
import { event } from '../runtime/core/routed-agent'
import { TopicId } from '../runtime/core/topic'
import { TypeSubscription } from '../runtime/in-process/type-subscription'
import { ActorBase, AgentActorBase } from './agent-actor-base'
import type { DefaultTypeAlias } from './orchestration-base'
import { OrchestrationBase } from './orchestration-base'

const logger = createDefaultLogger('GroupChat')

// region Messages and Types

/**
 * A message type to start a group chat.
 */
@experimental
export class GroupChatStartMessage {
  body: DefaultTypeAlias

  constructor(body: DefaultTypeAlias) {
    this.body = body
  }
}

/**
 * A request message type for agents in a group chat.
 */
@experimental
export class GroupChatRequestMessage {
  agentName: string

  constructor(agentName: string) {
    this.agentName = agentName
  }
}

/**
 * A response message type from agents in a group chat.
 */
@experimental
export class GroupChatResponseMessage {
  body: ChatMessageContent

  constructor(body: ChatMessageContent) {
    this.body = body
  }
}

/**
 * A result message type from the group chat manager.
 */
@experimental
export class GroupChatManagerResult<T> {
  result: T
  reason: string

  constructor(result: T, reason: string) {
    this.result = result
    this.reason = reason
  }
}

/**
 * A result message type from the group chat manager with a boolean result.
 */
@experimental
export class BooleanResult extends GroupChatManagerResult<boolean> {
  constructor(result: boolean, reason: string) {
    super(result, reason)
  }
}

/**
 * A result message type from the group chat manager with a string result.
 */
@experimental
export class StringResult extends GroupChatManagerResult<string> {
  constructor(result: string, reason: string) {
    super(result, reason)
  }
}

/**
 * A result message type from the group chat manager with a message result.
 */
@experimental
export class MessageResult extends GroupChatManagerResult<ChatMessageContent> {
  constructor(result: ChatMessageContent, reason: string) {
    super(result, reason)
  }
}

// endregion Messages and Types

// region GroupChatAgentActor

/**
 * An agent actor that process messages in a group chat.
 */
@experimental
export class GroupChatAgentActor extends AgentActorBase {
  @event()
  async _handleStartMessage(message: GroupChatStartMessage, _ctx: MessageContext): Promise<void> {
    logger.debug(`${this.id}: Received group chat start message.`)
    if (message.body instanceof ChatMessageContent) {
      this._messageCache.addMessage(message.body)
    } else if (Array.isArray(message.body) && message.body.every((m) => m instanceof ChatMessageContent)) {
      for (const m of message.body) {
        this._messageCache.addMessage(m)
      }
    } else {
      throw new Error(`Invalid message body type: ${typeof message.body}. Expected DefaultTypeAlias.`)
    }
  }

  @event()
  async _handleResponseMessage(message: GroupChatResponseMessage, _ctx: MessageContext): Promise<void> {
    logger.debug(`${this.id}: Received group chat response message.`)
    this._messageCache.addMessage(message.body)
  }

  @event()
  async _handleRequestMessage(message: GroupChatRequestMessage, ctx: MessageContext): Promise<void> {
    if (message.agentName !== this._agent.name) {
      return
    }

    logger.debug(`${this.id}: Received group chat request message.`)

    const response = await this._invokeAgent()

    logger.debug(`${this.id} responded with ${response}.`)

    await this.publishMessage(
      new GroupChatResponseMessage(response),
      new TopicId(this._internalTopicType, this.id.key),
      { cancellationToken: ctx.cancellationToken }
    )
  }
}

// Add message type registrations for the handlers
;(GroupChatAgentActor.prototype._handleStartMessage as any).targetTypes = [GroupChatStartMessage]
;(GroupChatAgentActor.prototype._handleResponseMessage as any).targetTypes = [GroupChatResponseMessage]
;(GroupChatAgentActor.prototype._handleRequestMessage as any).targetTypes = [GroupChatRequestMessage]

// endregion GroupChatAgentActor

// region GroupChatManager

/**
 * A group chat manager that manages the flow of a group chat.
 */
@experimental
export abstract class GroupChatManager {
  currentRound: number = 0
  maxRounds?: number

  humanResponseFunction?: (chatHistory: ChatHistory) => ChatMessageContent | Promise<ChatMessageContent>

  /**
   * Check if the group chat should request user input.
   */
  abstract shouldRequestUserInput(chatHistory: ChatHistory): Promise<BooleanResult>

  /**
   * Check if the group chat should terminate.
   */
  async shouldTerminate(_chatHistory: ChatHistory): Promise<BooleanResult> {
    this.currentRound += 1

    if (this.maxRounds !== undefined) {
      return new BooleanResult(
        this.currentRound > this.maxRounds,
        this.currentRound > this.maxRounds ? 'Maximum rounds reached.' : 'Not reached maximum rounds.'
      )
    }
    return new BooleanResult(false, 'No maximum rounds set.')
  }

  /**
   * Select the next agent to speak.
   */
  abstract selectNextAgent(
    chatHistory: ChatHistory,
    participantDescriptions: Map<string, string>
  ): Promise<StringResult>

  /**
   * Filter the results of the group chat.
   */
  abstract filterResults(chatHistory: ChatHistory): Promise<MessageResult>
}

/**
 * A round-robin group chat manager.
 */
@experimental
export class RoundRobinGroupChatManager extends GroupChatManager {
  currentIndex: number = 0

  constructor(options?: {
    maxRounds?: number
    humanResponseFunction?: (chatHistory: ChatHistory) => ChatMessageContent | Promise<ChatMessageContent>
  }) {
    super()
    if (options?.maxRounds !== undefined) {
      this.maxRounds = options.maxRounds
    }
    if (options?.humanResponseFunction !== undefined) {
      this.humanResponseFunction = options.humanResponseFunction
    }
  }

  async shouldRequestUserInput(_chatHistory: ChatHistory): Promise<BooleanResult> {
    return new BooleanResult(false, 'The default round-robin group chat manager does not request user input.')
  }

  async selectNextAgent(
    _chatHistory: ChatHistory,
    participantDescriptions: Map<string, string>
  ): Promise<StringResult> {
    // Handle both Map and plain object
    const keys =
      participantDescriptions instanceof Map
        ? Array.from(participantDescriptions.keys())
        : Object.keys(participantDescriptions)
    const nextAgent = keys[this.currentIndex]
    this.currentIndex = (this.currentIndex + 1) % keys.length
    return new StringResult(nextAgent, 'Round-robin selection.')
  }

  async filterResults(chatHistory: ChatHistory): Promise<MessageResult> {
    return new MessageResult(
      chatHistory.messages[chatHistory.messages.length - 1],
      'The last message in the chat history is the result in the default round-robin group chat manager.'
    )
  }
}

// endregion GroupChatManager

// region GroupChatManagerActor

/**
 * A group chat manager actor.
 */
@experimental
export class GroupChatManagerActor extends ActorBase {
  private _manager: GroupChatManager
  private _internalTopicType: string
  private _chatHistory: ChatHistory
  private _participantDescriptions: Map<string, string>
  private _resultCallback?: (result: DefaultTypeAlias) => void | Promise<void>

  constructor(options: {
    manager: GroupChatManager
    internalTopicType: string
    participantDescriptions: Map<string, string>
    exceptionCallback: (exception: Error) => void
    resultCallback?: (result: DefaultTypeAlias) => void | Promise<void>
  }) {
    super('An actor for the group chat manager.', options.exceptionCallback)

    this._manager = options.manager
    this._internalTopicType = options.internalTopicType
    this._chatHistory = new ChatHistory()
    this._participantDescriptions = options.participantDescriptions
    this._resultCallback = options.resultCallback
  }

  @event()
  async _handleStartMessage(message: GroupChatStartMessage, ctx: MessageContext): Promise<void> {
    logger.debug(`${this.id}: Received group chat start message.`)
    if (message.body instanceof ChatMessageContent) {
      this._chatHistory.addMessage(message.body)
    } else if (Array.isArray(message.body) && message.body.every((m) => m instanceof ChatMessageContent)) {
      for (const m of message.body) {
        this._chatHistory.addMessage(m)
      }
    } else {
      throw new Error(`Invalid message body type: ${typeof message.body}. Expected DefaultTypeAlias.`)
    }

    await this._determineStateAndTakeAction(ctx.cancellationToken)
  }

  @event()
  async _handleResponseMessage(message: GroupChatResponseMessage, ctx: MessageContext): Promise<void> {
    if (message.body.role !== AuthorRole.USER) {
      this._chatHistory.addMessage(
        new ChatMessageContent({
          role: AuthorRole.USER,
          content: `Transferred to ${message.body.name}`,
        })
      )
    }
    this._chatHistory.addMessage(message.body)

    await this._determineStateAndTakeAction(ctx.cancellationToken)
  }

  private async _determineStateAndTakeAction(cancellationToken: CancellationToken): Promise<void> {
    try {
      // User input state
      const chatHistoryCopy = new ChatHistory([...this._chatHistory.messages])
      const shouldRequestUserInput = await this._manager.shouldRequestUserInput(chatHistoryCopy)
      if (shouldRequestUserInput.result && this._manager.humanResponseFunction) {
        logger.debug(`Group chat manager requested user input. Reason: ${shouldRequestUserInput.reason}`)
        const userInputMessage = await this._callHumanResponseFunction()
        this._chatHistory.addMessage(userInputMessage)
        await this.publishMessage(
          new GroupChatResponseMessage(userInputMessage),
          new TopicId(this._internalTopicType, this.id.key),
          { cancellationToken }
        )
        logger.debug('User input received and added to chat history.')
      }

      // Determine if the group chat should terminate
      const shouldTerminate = await this._manager.shouldTerminate(new ChatHistory([...this._chatHistory.messages]))
      if (shouldTerminate.result) {
        logger.debug(`Group chat manager decided to terminate the group chat. Reason: ${shouldTerminate.reason}`)
        if (this._resultCallback) {
          const result = await this._manager.filterResults(new ChatHistory([...this._chatHistory.messages]))
          result.result.metadata = result.result.metadata || {}
          result.result.metadata['termination_reason'] = shouldTerminate.reason
          result.result.metadata['filter_result_reason'] = result.reason
          await this._resultCallback(result.result)
        }
        return
      }

      // Select the next agent to speak if the group chat is not terminating
      const nextAgent = await this._manager.selectNextAgent(
        new ChatHistory([...this._chatHistory.messages]),
        this._participantDescriptions
      )
      logger.debug(
        `Group chat manager selected agent: ${nextAgent.result} on round ${this._manager.currentRound}. ` +
          `Reason: ${nextAgent.reason}`
      )

      await this.publishMessage(
        new GroupChatRequestMessage(nextAgent.result),
        new TopicId(this._internalTopicType, this.id.key),
        { cancellationToken }
      )
    } catch (error) {
      this._exceptionCallback(error as Error)
      logger.error(`Exception occurred in group chat manager ${this.id}:`, error)
      throw error
    }
  }

  private async _callHumanResponseFunction(): Promise<ChatMessageContent> {
    if (!this._manager.humanResponseFunction) {
      throw new Error('Human response function is not set.')
    }
    const result = this._manager.humanResponseFunction(new ChatHistory([...this._chatHistory.messages]))
    if (result instanceof Promise) {
      return await result
    }
    return result
  }
}

// Add message type registrations for the handlers
;(GroupChatManagerActor.prototype._handleStartMessage as any).targetTypes = [GroupChatStartMessage]
;(GroupChatManagerActor.prototype._handleResponseMessage as any).targetTypes = [GroupChatResponseMessage]

// endregion GroupChatManagerActor

// region GroupChatOrchestration

/**
 * A group chat multi-agent pattern orchestration.
 */
@experimental
export class GroupChatOrchestration<TIn, TOut> extends OrchestrationBase<TIn, TOut> {
  private _manager: GroupChatManager

  constructor(options: {
    members: Agent[]
    manager: GroupChatManager
    name?: string
    description?: string
    inputTransform?: (input: TIn) => DefaultTypeAlias | Promise<DefaultTypeAlias>
    outputTransform?: (output: DefaultTypeAlias) => TOut | Promise<TOut>
    agentResponseCallback?: (response: DefaultTypeAlias) => void | Promise<void>
    streamingAgentResponseCallback?: (response: StreamingChatMessageContent, isFinal: boolean) => void | Promise<void>
  }) {
    // Validate all members have descriptions
    for (const member of options.members) {
      if (!member.description) {
        throw new Error('All members must have a description.')
      }
    }

    super({
      members: options.members,
      name: options.name,
      description: options.description,
      inputTransform: options.inputTransform,
      outputTransform: options.outputTransform,
      agentResponseCallback: options.agentResponseCallback,
      streamingAgentResponseCallback: options.streamingAgentResponseCallback,
    })

    this._manager = options.manager
  }

  protected async _start(
    task: DefaultTypeAlias,
    runtime: CoreRuntime,
    internalTopicType: string,
    cancellationToken: CancellationToken
  ): Promise<void> {
    // Send start messages to all agent actors first
    const sendStartMessagePromises = this._members.map(async (agent) => {
      const targetActorId = await runtime.get(this._getAgentActorType(agent, internalTopicType))
      await runtime.sendMessage(new GroupChatStartMessage(task), targetActorId, { cancellationToken })
    })

    await Promise.all(sendStartMessagePromises)

    // Send the start message to the manager actor
    const targetActorId = await runtime.get(this._getManagerActorType(internalTopicType))
    await runtime.sendMessage(new GroupChatStartMessage(task), targetActorId, { cancellationToken })
  }

  protected async _prepare(
    runtime: CoreRuntime,
    options: {
      internalTopicType: string
      exceptionCallback: (exception: Error) => void
      resultCallback: (result: DefaultTypeAlias) => Promise<void>
    }
  ): Promise<void> {
    await this._registerMembers(runtime, options.internalTopicType, options.exceptionCallback)
    await this._registerManager(runtime, options.internalTopicType, options.exceptionCallback, options.resultCallback)
    await this._addSubscriptions(runtime, options.internalTopicType)
  }

  private async _registerMembers(
    runtime: CoreRuntime,
    internalTopicType: string,
    exceptionCallback: (exception: Error) => void
  ): Promise<void> {
    const registrationPromises = this._members.map((agent) =>
      GroupChatAgentActor.register(
        runtime as any,
        this._getAgentActorType(agent, internalTopicType),
        () =>
          new GroupChatAgentActor({
            agent,
            internalTopicType,
            exceptionCallback,
            agentResponseCallback: this._agentResponseCallback,
            streamingAgentResponseCallback: this._streamingAgentResponseCallback,
          })
      )
    )

    await Promise.all(registrationPromises)
  }

  private async _registerManager(
    runtime: CoreRuntime,
    internalTopicType: string,
    exceptionCallback: (exception: Error) => void,
    resultCallback?: (result: DefaultTypeAlias) => Promise<void>
  ): Promise<void> {
    await GroupChatManagerActor.register(runtime as any, this._getManagerActorType(internalTopicType), () => {
      const participantDescriptions = new Map<string, string>()
      for (const agent of this._members) {
        participantDescriptions.set(agent.name, agent.description!)
      }

      return new GroupChatManagerActor({
        manager: this._manager,
        internalTopicType,
        participantDescriptions,
        exceptionCallback,
        resultCallback,
      })
    })
  }

  private async _addSubscriptions(runtime: CoreRuntime, internalTopicType: string): Promise<void> {
    const subscriptions: TypeSubscription[] = []

    for (const agent of this._members) {
      subscriptions.push(new TypeSubscription(internalTopicType, this._getAgentActorType(agent, internalTopicType)))
    }
    subscriptions.push(new TypeSubscription(internalTopicType, this._getManagerActorType(internalTopicType)))

    await Promise.all(subscriptions.map((sub) => runtime.addSubscription(sub)))
  }

  private _getAgentActorType(agent: Agent, internalTopicType: string): string {
    return `${agent.name}_${internalTopicType}`
  }

  private _getManagerActorType(internalTopicType: string): string {
    return `GroupChatManagerActor_${internalTopicType}`
  }
}

// endregion GroupChatOrchestration
