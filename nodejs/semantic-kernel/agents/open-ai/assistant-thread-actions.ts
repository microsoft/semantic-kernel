import type OpenAI from 'openai'
import type { CodeInterpreterTool, FileSearchTool } from 'openai/resources/beta/index'
import type { Message, MessageListParams } from 'openai/resources/beta/threads/messages'
import type {
  MessageCreationStepDetails,
  RunStep,
  RunStepDeltaEvent,
  ToolCallDeltaObject,
  ToolCallsStepDetails,
} from 'openai/resources/beta/threads/runs/steps'
import { ChatHistory } from '../../contents/chat-history'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { FileReferenceContent } from '../../contents/file-reference-content'
import { FunctionCallContent } from '../../contents/function-call-content'
import { FunctionResultContent } from '../../contents/function-result-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { StreamingFileReferenceContent } from '../../contents/streaming-file-reference-content'
import { AuthorRole } from '../../contents/utils/author-role'
import { AgentExecutionException, AgentInvokeException } from '../../exceptions/agent-exceptions'
import { KernelFunctionMetadata } from '../../functions/kernel-function-metadata'
import { Kernel } from '../../kernel'
import { createDefaultLogger, Logger } from '../../utils/logger'
import type { OpenAIAssistantAgent } from './openai-assistant-agent'

const logger: Logger = createDefaultLogger('AssistantThreadActions')

/**
 * Result from handling streaming function calls.
 */
export interface FunctionActionResult {
  functionCallStreamingContent: StreamingChatMessageContent
  functionResultStreamingContent: StreamingChatMessageContent
  toolOutputs: Array<{ tool_call_id: string; output: string }>
}

/**
 * Configuration and defaults associated with polling behavior for Assistant API requests.
 */
export interface RunPollingOptions {
  defaultPollingInterval: number // milliseconds
  defaultPollingBackoff: number // milliseconds
  defaultPollingBackoffThreshold: number
  defaultMessageSynchronizationDelay: number // milliseconds
  runPollingInterval: number // milliseconds
  runPollingBackoff: number // milliseconds
  runPollingBackoffThreshold: number
  messageSynchronizationDelay: number // milliseconds
  runPollingTimeout: number // milliseconds

  getPollingInterval(iterationCount: number): number
}

/**
 * Default polling options for runs.
 */
export const DEFAULT_RUN_POLLING_OPTIONS: RunPollingOptions = {
  defaultPollingInterval: 250,
  defaultPollingBackoff: 1000,
  defaultPollingBackoffThreshold: 2,
  defaultMessageSynchronizationDelay: 250,
  runPollingInterval: 250,
  runPollingBackoff: 1000,
  runPollingBackoffThreshold: 2,
  messageSynchronizationDelay: 250,
  runPollingTimeout: 60000, // 1 minute

  getPollingInterval(iterationCount: number): number {
    return iterationCount > this.runPollingBackoffThreshold ? this.runPollingBackoff : this.runPollingInterval
  },
}

/**
 * Assistant Thread Actions class.
 *
 * Provides static methods for interacting with OpenAI Assistant threads,
 * including message creation, invocation, streaming, and message retrieval.
 */
export class AssistantThreadActions {
  /**
   * Statuses that indicate a run is still in progress and should continue polling.
   */
  static readonly POLLING_STATUS = ['queued', 'in_progress', 'cancelling']

  /**
   * Statuses that indicate a run has encountered an error.
   */
  static readonly ERROR_MESSAGE_STATES = ['failed', 'cancelled', 'expired', 'incomplete']

  /**
   * Tool metadata for file attachments.
   */
  static readonly TOOL_METADATA: Record<string, any[]> = {
    file_search: [{ type: 'file_search' }],
    code_interpreter: [{ type: 'code_interpreter' }],
  }

  // #region Messaging Handling Methods

  /**
   * Create a message in the thread.
   *
   * @param client - The OpenAI client to use.
   * @param threadId - The ID of the thread.
   * @param message - The message to create (string or ChatMessageContent).
   * @param allowedMessageRoles - Allowed message roles. Defaults to ['user', 'assistant'].
   * @param kwargs - Additional keyword arguments for message creation.
   * @returns The created message, or null if the message contains function calls.
   */
  static async createMessage(
    client: OpenAI,
    threadId: string,
    message: string | ChatMessageContent,
    allowedMessageRoles?: string[],
    kwargs?: Record<string, any>
  ): Promise<Message | null> {
    let messageContent: ChatMessageContent

    if (typeof message === 'string') {
      messageContent = new ChatMessageContent({
        role: AuthorRole.USER,
        content: message,
      })
    } else {
      messageContent = message
    }

    // Skip messages containing function calls
    if (messageContent.items.some((item) => item instanceof FunctionCallContent)) {
      return null
    }

    // Set default allowed roles if not provided
    const allowedRoles = allowedMessageRoles ?? [AuthorRole.USER, AuthorRole.ASSISTANT]

    if (!allowedRoles.includes(messageContent.role) && messageContent.role !== AuthorRole.TOOL) {
      throw new AgentExecutionException(
        `Invalid message role '${messageContent.role}'. Allowed roles are ${allowedRoles.join(', ')}.`
      )
    }

    const messageContents = this._getMessageContents(messageContent)

    return await client.beta.threads.messages.create(threadId, {
      role: messageContent.role === AuthorRole.TOOL ? 'assistant' : (messageContent.role as 'user' | 'assistant'),
      content: messageContents as any,
      ...(kwargs || {}),
    })
  }

  // #endregion

  // #region Invocation Methods

  /**
   * Invoke the assistant and yield message responses.
   *
   * @param options - Invocation options.
   * @yields Tuples of [isVisible, ChatMessageContent].
   */
  static async *invoke(options: {
    agent: OpenAIAssistantAgent
    threadId: string
    additionalInstructions?: string
    additionalMessages?: ChatMessageContent[]
    arguments?: Record<string, any>
    instructionsOverride?: string
    kernel?: Kernel
    maxCompletionTokens?: number
    maxPromptTokens?: number
    metadata?: Record<string, string>
    model?: string
    parallelToolCalls?: boolean
    reasoningEffort?: 'low' | 'medium' | 'high'
    responseFormat?: any
    temperature?: number
    topP?: number
    truncationStrategy?: any
    pollingOptions?: RunPollingOptions
  }): AsyncIterable<[boolean, ChatMessageContent]> {
    const {
      agent,
      threadId,
      additionalInstructions,
      additionalMessages,
      arguments: args = {},
      instructionsOverride,
      kernel = agent.kernel,
      maxCompletionTokens,
      maxPromptTokens,
      metadata,
      model,
      parallelToolCalls,
      reasoningEffort,
      responseFormat,
      temperature,
      topP,
      truncationStrategy,
      pollingOptions = DEFAULT_RUN_POLLING_OPTIONS,
    } = options

    const toolsList = this._getTools(agent, kernel)

    const baseInstructions = await agent.formatInstructions(kernel, args as any)

    let mergedInstructions
    if (instructionsOverride !== undefined) {
      mergedInstructions = instructionsOverride
    } else if (baseInstructions && additionalInstructions) {
      mergedInstructions = `${baseInstructions}\n\n${additionalInstructions}`
    } else {
      mergedInstructions = baseInstructions || additionalInstructions || ''
    }

    // Form run options
    const runOptions = this._generateOptions({
      agent,
      model,
      responseFormat,
      temperature,
      topP,
      metadata,
      parallelToolCallsEnabled: parallelToolCalls,
      truncationMessageCount: truncationStrategy,
      maxCompletionTokens,
      maxPromptTokens,
      additionalMessages,
      reasoningEffort,
    })

    // Filter out undefined values
    const filteredRunOptions = Object.fromEntries(
      Object.entries(runOptions).filter(([_, v]) => v !== undefined && v !== null)
    )

    let run = await agent.client.beta.threads.runs.create(threadId, {
      assistant_id: agent.id,
      instructions: mergedInstructions || agent.instructions,
      tools: toolsList as any,
      ...filteredRunOptions,
    })

    const processedStepIds = new Set<string>()
    const functionSteps: Map<string, FunctionCallContent> = new Map()

    while (run.status !== 'completed') {
      run = await this._pollRunStatus(agent, run, threadId, pollingOptions)

      if (AssistantThreadActions.ERROR_MESSAGE_STATES.includes(run.status)) {
        const errorMessage = run.last_error?.message || ''
        const incompleteDetails = run.incomplete_details?.reason || ''
        throw new AgentInvokeException(
          `Run failed with status: '${run.status}' for agent '${agent.name}' and thread '${threadId}' ` +
            `with error: ${errorMessage} or incomplete details: ${incompleteDetails}`
        )
      }

      // Check if function calling required
      if (run.status === 'requires_action') {
        logger.debug(`Run [${run.id}] requires action for agent '${agent.name}' and thread '${threadId}'`)
        const fccs = this._getFunctionCallContents(run, functionSteps)
        if (fccs.length > 0) {
          logger.debug(
            `Yielding function call content for agent '${agent.name}' and thread '${threadId}', visibility False`
          )
          yield [false, this._generateFunctionCallContent(agent.name, fccs)]

          const chatHistory = new ChatHistory()
          await this._invokeFunctionCalls(kernel, fccs, chatHistory, args)

          const toolOutputs = this._formatToolOutputs(fccs, chatHistory)
          await agent.client.beta.threads.runs.submitToolOutputs(threadId, run.id, {
            tool_outputs: toolOutputs as any,
          })
          logger.debug(`Submitted tool outputs for agent '${agent.name}' and thread '${threadId}'`)
          continue
        }
      }

      const stepsResponse = await agent.client.beta.threads.runs.steps.list(threadId, run.id)
      logger.debug(`Called for steps_response for run [${run.id}] agent '${agent.name}' and thread '${threadId}'`)
      const steps: RunStep[] = stepsResponse.data

      // Sort steps: tool_calls first, then message_creation, with completed_at as tiebreaker
      const completedStepsToProcess = steps
        .filter((s) => s.completed_at !== null && !processedStepIds.has(s.id))
        .sort((a, b) => {
          const aType = a.type === 'tool_calls' ? 0 : 1
          const bType = b.type === 'tool_calls' ? 0 : 1
          if (aType !== bType) return aType - bType
          return (a.completed_at || 0) - (b.completed_at || 0)
        })

      logger.debug(
        `Completed steps to process for run [${run.id}] agent '${agent.name}' and thread '${threadId}' ` +
          `with length ${completedStepsToProcess.length}`
      )

      let messageCount = 0
      for (const completedStep of completedStepsToProcess) {
        if (completedStep.type === 'tool_calls') {
          logger.debug(
            `Entering step type tool_calls for run [${run.id}], agent '${agent.name}' and thread '${threadId}'`
          )

          const toolCallDetails = completedStep.step_details as ToolCallsStepDetails
          for (const toolCall of toolCallDetails.tool_calls) {
            let isVisible = false
            let content: ChatMessageContent | null = null

            if (toolCall.type === 'code_interpreter') {
              logger.debug(
                `Entering step type tool_calls for run [${run.id}], [code_interpreter] for agent '${agent.name}' and thread '${threadId}'`
              )
              content = this._generateCodeInterpreterContent(agent.name, (toolCall as any).code_interpreter.input)
              isVisible = true
            } else if (toolCall.type === 'function') {
              logger.debug(
                `Entering step type tool_calls for run [${run.id}], [function] for agent '${agent.name}' and thread '${threadId}'`
              )
              const functionStep = functionSteps.get(toolCall.id)
              if (functionStep) {
                content = this._generateFunctionResultContent(agent.name, functionStep, toolCall as any)
              }
            }

            if (content) {
              messageCount++
              logger.debug(
                `Yielding tool_message for run [${run.id}], agent '${agent.name}' and thread '${threadId}' ` +
                  `and message count ${messageCount}, is_visible ${isVisible}`
              )
              yield [isVisible, content]
            }
          }
        } else if (completedStep.type === 'message_creation') {
          logger.debug(
            `Entering step type message_creation for run [${run.id}], agent '${agent.name}' and thread '${threadId}'`
          )
          const messageCreationDetails = completedStep.step_details as MessageCreationStepDetails
          const message = await this._retrieveMessage(
            agent,
            threadId,
            messageCreationDetails.message_creation.message_id
          )
          if (message) {
            const content = this._generateMessageContent(agent.name, message, completedStep)
            if (content && content.items.length > 0) {
              messageCount++
              logger.debug(
                `Yielding message_creation for run [${run.id}], agent '${agent.name}' and thread '${threadId}' ` +
                  `and message count ${messageCount}, is_visible true`
              )
              yield [true, content]
            }
          }
        }
        processedStepIds.add(completedStep.id)
      }
    }
  }

  /**
   * Invoke the assistant with streaming responses.
   *
   * @param options - Streaming invocation options.
   * @yields StreamingChatMessageContent.
   */
  static async *invokeStream(options: {
    agent: OpenAIAssistantAgent
    threadId: string
    additionalInstructions?: string
    additionalMessages?: ChatMessageContent[]
    arguments?: Record<string, any>
    instructionsOverride?: string
    kernel?: Kernel
    maxCompletionTokens?: number
    maxPromptTokens?: number
    metadata?: Record<string, string>
    model?: string
    outputMessages?: ChatMessageContent[]
    parallelToolCalls?: boolean
    reasoningEffort?: 'low' | 'medium' | 'high'
    responseFormat?: any
    temperature?: number
    topP?: number
    truncationStrategy?: any
  }): AsyncIterable<StreamingChatMessageContent> {
    const {
      agent,
      threadId,
      additionalInstructions,
      additionalMessages,
      arguments: args = {},
      instructionsOverride,
      kernel = agent.kernel,
      maxCompletionTokens,
      maxPromptTokens,
      metadata,
      model,
      outputMessages,
      parallelToolCalls,
      reasoningEffort,
      responseFormat,
      temperature,
      topP,
      truncationStrategy,
    } = options

    const toolsList = this._getTools(agent, kernel)

    const baseInstructions = await agent.formatInstructions(kernel, args as any)

    let mergedInstructions
    if (instructionsOverride !== undefined) {
      mergedInstructions = instructionsOverride
    } else if (baseInstructions && additionalInstructions) {
      mergedInstructions = `${baseInstructions}\n\n${additionalInstructions}`
    } else {
      mergedInstructions = baseInstructions || additionalInstructions || ''
    }

    // Form run options
    const runOptions = this._generateOptions({
      agent,
      model,
      responseFormat,
      temperature,
      topP,
      metadata,
      parallelToolCallsEnabled: parallelToolCalls,
      truncationMessageCount: truncationStrategy,
      maxCompletionTokens,
      maxPromptTokens,
      additionalMessages,
      reasoningEffort,
    })

    // Filter out undefined values
    const filteredRunOptions = Object.fromEntries(
      Object.entries(runOptions).filter(([_, v]) => v !== undefined && v !== null)
    )

    let stream = agent.client.beta.threads.runs.stream(threadId, {
      assistant_id: agent.id,
      instructions: mergedInstructions || agent.instructions,
      tools: toolsList as any,
      ...filteredRunOptions,
    })

    const functionSteps: Map<string, FunctionCallContent> = new Map()
    const activeMessages: Map<string, RunStep> = new Map()

    while (true) {
      let shouldBreak = false

      for await (const event of stream) {
        if (event.event === 'thread.run.created') {
          const run = event.data
          logger.info(`Assistant run created with ID: ${run.id}`)
        } else if (event.event === 'thread.run.in_progress') {
          const run = event.data
          logger.info(`Assistant run in progress with ID: ${run.id}`)
        } else if (event.event === 'thread.message.delta') {
          const content = this._generateStreamingMessageContent(agent.name, event.data as any)
          yield content
        } else if (event.event === 'thread.run.step.completed') {
          const stepCompleted = event.data as RunStep
          logger.info(`Run step completed with ID: ${event.data.id}`)
          if (stepCompleted.step_details.type === 'message_creation') {
            const messageCreation = stepCompleted.step_details as MessageCreationStepDetails
            const messageId = messageCreation.message_creation.message_id
            if (!activeMessages.has(messageId)) {
              activeMessages.set(messageId, event.data)
            }
          }
        } else if (event.event === 'thread.run.step.delta') {
          const runStepEvent = event.data as RunStepDeltaEvent
          const details = runStepEvent.delta.step_details
          if (!details) {
            continue
          }

          const stepDetails = runStepEvent.delta.step_details
          if (stepDetails && stepDetails.type === 'tool_calls' && (stepDetails as ToolCallDeltaObject).tool_calls) {
            const toolCalls = (stepDetails as ToolCallDeltaObject).tool_calls || []
            for (const toolCall of toolCalls) {
              let toolContent: StreamingChatMessageContent | null = null
              let contentIsVisible = false

              if (toolCall.type === 'code_interpreter') {
                toolContent = this._generateStreamingCodeInterpreterContent(agent.name, stepDetails as any)
                contentIsVisible = true
              }

              if (toolContent) {
                if (outputMessages && !contentIsVisible) {
                  outputMessages.push(toolContent)
                }
                if (contentIsVisible) {
                  yield toolContent
                }
              }
            }
          }
        } else if (event.event === 'thread.run.requires_action') {
          const run = event.data as any
          const actionResult = await this._handleStreamingRequiresAction(agent.name, kernel, run, functionSteps, args)
          if (!actionResult) {
            throw new AgentInvokeException(
              `Function call required but no function steps found for agent '${agent.name}' thread: ${threadId}.`
            )
          }

          for (const content of [
            actionResult.functionCallStreamingContent,
            actionResult.functionResultStreamingContent,
          ]) {
            if (content && outputMessages) {
              outputMessages.push(content)
            }
          }

          stream = agent.client.beta.threads.runs.submitToolOutputsStream(threadId, run.id, {
            tool_outputs: actionResult.toolOutputs as any,
          })
          shouldBreak = true
          break
        } else if (event.event === 'thread.run.completed') {
          const run = event.data
          logger.info(`Run completed with ID: ${run.id}`)
          if (activeMessages.size > 0) {
            for (const [id, step] of activeMessages) {
              const message = await this._retrieveMessage(agent, threadId, id)

              if (message && message.content) {
                const content = this._generateFinalStreamingMessageContent(agent.name, message, step)
                if (outputMessages) {
                  outputMessages.push(content)
                }
              }
            }
          }
          return
        } else if (event.event === 'thread.run.failed') {
          const run = event.data as any
          const errorMessage = run.last_error?.message || ''
          throw new AgentInvokeException(
            `Run failed with status: '${run.status}' for agent '${agent.name}' and thread '${threadId}' ` +
              `with error: ${errorMessage}`
          )
        }
      }

      if (!shouldBreak) {
        break
      }
    }
  }

  /**
   * Handle the requires_action event for a streaming run.
   */
  private static async _handleStreamingRequiresAction(
    agentName: string,
    kernel: Kernel,
    run: any,
    functionSteps: Map<string, FunctionCallContent>,
    arguments_: Record<string, any>
  ): Promise<FunctionActionResult | null> {
    const fccs = this._getFunctionCallContents(run, functionSteps)
    if (fccs.length > 0) {
      const functionCallStreamingContent = this._generateFunctionCallStreamingContent(agentName, fccs)
      const chatHistory = new ChatHistory()
      const results = await this._invokeFunctionCalls(kernel, fccs, chatHistory, arguments_)

      const functionResultStreamingContent = this._mergeStreamingFunctionResults(
        chatHistory.messages.slice(-results.length),
        agentName
      )
      const toolOutputs = this._formatToolOutputs(fccs, chatHistory)
      return {
        functionCallStreamingContent,
        functionResultStreamingContent,
        toolOutputs,
      }
    }
    return null
  }

  // #endregion

  /**
   * Get messages from the thread.
   *
   * @param client - The OpenAI client.
   * @param threadId - The ID of the thread.
   * @param sortOrder - The sort order ('asc' or 'desc').
   * @yields ChatMessageContent.
   */
  static async *getMessages(
    client: OpenAI,
    threadId: string,
    sortOrder?: 'asc' | 'desc'
  ): AsyncIterable<ChatMessageContent> {
    const agentNames: Map<string, string> = new Map()
    let lastId: string | undefined = undefined

    while (true) {
      const messagesParams: MessageListParams = {
        order: sortOrder,
      }
      if (lastId) {
        messagesParams.after = lastId
      }

      const messages = await client.beta.threads.messages.list(threadId, messagesParams)

      if (!messages || messages.data.length === 0) {
        break
      }

      for (const message of messages.data) {
        lastId = message.id

        if (message.assistant_id && message.assistant_id.trim() && !agentNames.has(message.assistant_id)) {
          const agent = await client.beta.assistants.retrieve(message.assistant_id)
          if (agent.name && agent.name.trim()) {
            agentNames.set(agent.id, agent.name)
          }
        }

        const assistantName = agentNames.get(message.assistant_id || '') || message.assistant_id || message.id
        const content = this._generateMessageContent(assistantName, message)

        if (content.items.length > 0) {
          yield content
        }
      }

      if (!messages.has_more) {
        break
      }
    }
  }

  /**
   * Retrieve a message from a thread with retry logic.
   */
  private static async _retrieveMessage(
    agent: OpenAIAssistantAgent,
    threadId: string,
    messageId: string
  ): Promise<Message | null> {
    let message: Message | null = null
    let count = 0
    const maxRetries = 3
    const pollingOptions = (agent as any).pollingOptions || DEFAULT_RUN_POLLING_OPTIONS

    while (count < maxRetries) {
      try {
        message = await agent.client.beta.threads.messages.retrieve(threadId, messageId)
        break
      } catch (ex) {
        logger.error(`Failed to retrieve message ${messageId} from thread ${threadId}: ${ex}`)
        count++
        if (count >= maxRetries) {
          logger.error(`Max retries reached. Unable to retrieve message ${messageId} from thread ${threadId}.`)
          break
        }
        const backoffTime = pollingOptions.messageSynchronizationDelay * Math.pow(2, count)
        await this._sleep(backoffTime)
      }
    }
    return message
  }

  /**
   * Invoke function calls using the kernel.
   */
  private static async _invokeFunctionCalls(
    kernel: Kernel,
    fccs: FunctionCallContent[],
    chatHistory: ChatHistory,
    arguments_: Record<string, any>
  ): Promise<any[]> {
    return await Promise.all(
      fccs.map((functionCall) =>
        kernel.invokeFunctionCall({
          functionCall: functionCall as any,
          chatHistory,
          arguments: arguments_ as any,
        })
      )
    )
  }

  /**
   * Format tool outputs for submission.
   */
  private static _formatToolOutputs(
    fccs: FunctionCallContent[],
    chatHistory: ChatHistory
  ): Array<{ tool_call_id: string; output: string }> {
    const toolCallLookup = new Map<string, FunctionResultContent>()

    for (const message of chatHistory.messages) {
      for (const toolCall of message.items) {
        if (toolCall instanceof FunctionResultContent && toolCall.callId) {
          toolCallLookup.set(toolCall.callId, toolCall)
        }
      }
    }

    return fccs
      .filter((fcc) => fcc.id && toolCallLookup.has(fcc.id))
      .map((fcc) => ({
        tool_call_id: fcc.id!,
        output: String(toolCallLookup.get(fcc.id!)!.result || ''),
      }))
  }

  /**
   * Poll the run status.
   */
  private static async _pollRunStatus(
    agent: OpenAIAssistantAgent,
    run: any,
    threadId: string,
    pollingOptions: RunPollingOptions
  ): Promise<any> {
    logger.info(`Polling run status: ${run.id}, threadId: ${threadId}`)

    try {
      run = await this._withTimeout(
        this._pollLoop(agent, run, threadId, pollingOptions),
        pollingOptions.runPollingTimeout,
        `Polling timed out for run id: '${run.id}' and thread id: '${threadId}' after waiting ${pollingOptions.runPollingTimeout}ms.`
      )
    } catch (error) {
      logger.error(String(error))
      throw new AgentInvokeException(String(error))
    }

    logger.info(`Polled run status: ${run.status}, ${run.id}, threadId: ${threadId}`)
    return run
  }

  /**
   * Internal polling loop.
   */
  private static async _pollLoop(
    agent: OpenAIAssistantAgent,
    run: any,
    threadId: string,
    pollingOptions: RunPollingOptions
  ): Promise<any> {
    let count = 0

    while (true) {
      await this._sleep(pollingOptions.getPollingInterval(count))
      count++

      try {
        run = await agent.client.beta.threads.runs.retrieve(threadId, run.id)
      } catch (e) {
        logger.warn(`Failed to retrieve run for run id: '${run.id}' and thread id: '${threadId}': ${e}`)
        // Retry anyway
      }

      if (!AssistantThreadActions.POLLING_STATUS.includes(run.status)) {
        break
      }
    }

    return run
  }

  /**
   * Merge run-time options with agent-level options.
   * Run-level parameters take precedence.
   */
  private static _mergeOptions(options: {
    agent: OpenAIAssistantAgent
    model?: string
    responseFormat?: any
    temperature?: number
    topP?: number
    metadata?: Record<string, string>
    [key: string]: any
  }): Record<string, any> {
    const { agent, model, responseFormat, temperature, topP, metadata, ...kwargs } = options
    return {
      model: model !== undefined ? model : (agent.definition as any).model,
      responseFormat: responseFormat !== undefined ? responseFormat : null,
      temperature: temperature !== undefined ? temperature : (agent.definition as any).temperature,
      topP: topP !== undefined ? topP : (agent.definition as any).top_p,
      metadata: metadata !== undefined ? metadata : (agent.definition as any).metadata,
      ...kwargs,
    }
  }

  /**
   * Generate a dictionary of options that can be passed directly to create_run.
   */
  private static _generateOptions(kwargs: Record<string, any>): Record<string, any> {
    const merged = this._mergeOptions({ ...kwargs, agent: kwargs.agent })
    const truncCount = merged.truncationMessageCount
    const maxCompletionTokens = merged.maxCompletionTokens
    const maxPromptTokens = merged.maxPromptTokens
    const parallelToolCalls = merged.parallelToolCallsEnabled
    const additionalMessages = this._translateAdditionalMessages(merged.additionalMessages)

    return {
      model: merged.model,
      top_p: merged.topP,
      response_format: merged.responseFormat,
      temperature: merged.temperature,
      truncation_strategy: truncCount,
      metadata: merged.metadata,
      max_completion_tokens: maxCompletionTokens,
      max_prompt_tokens: maxPromptTokens,
      parallel_tool_calls: parallelToolCalls,
      additional_messages: additionalMessages,
      reasoning_effort: merged.reasoningEffort,
    }
  }

  /**
   * Translate additional messages to the required format.
   */
  private static _translateAdditionalMessages(messages?: ChatMessageContent[]): any[] | undefined {
    if (!messages || messages.length === 0) {
      return undefined
    }
    return this._formAdditionalMessages(messages)
  }

  /**
   * Form the additional messages for the specified thread.
   */
  private static _formAdditionalMessages(messages: ChatMessageContent[]): any[] | undefined {
    if (!messages || messages.length === 0) {
      return undefined
    }

    const additionalMessages = []
    for (const message of messages) {
      if (!message.content) {
        continue
      }

      const messageWithAll: any = {
        content: message.content,
        role: message.role === AuthorRole.ASSISTANT ? 'assistant' : 'user',
        attachments: message.items.length > 0 ? this._getAttachments(message) : undefined,
        metadata: message.metadata ? this._getMetadata(message) : undefined,
      }
      additionalMessages.push(messageWithAll)
    }
    return additionalMessages
  }

  /**
   * Get attachments from a message.
   */
  private static _getAttachments(message: ChatMessageContent): any[] {
    return message.items
      .filter(
        (item) =>
          (item instanceof FileReferenceContent || item instanceof StreamingFileReferenceContent) &&
          item.fileId !== undefined
      )
      .map((fileContent) => ({
        file_id: (fileContent as FileReferenceContent | StreamingFileReferenceContent).fileId,
        tools: this._getToolDefinition((fileContent as any).tools || []),
        data_source: (fileContent as any).dataSource || undefined,
      }))
  }

  /**
   * Get metadata for an agent message.
   */
  private static _getMetadata(message: ChatMessageContent): Record<string, string> {
    return Object.fromEntries(
      Object.entries(message.metadata || {}).map(([k, v]) => [k, v !== null && v !== undefined ? String(v) : ''])
    )
  }

  /**
   * Get tool definition for file attachments.
   */
  private static _getToolDefinition(tools: any[]): any[] {
    if (!tools || tools.length === 0) {
      return []
    }
    const toolDefinitions: any[] = []
    for (const tool of tools) {
      const toolDef = AssistantThreadActions.TOOL_METADATA[tool]
      if (toolDef) {
        toolDefinitions.push(...toolDef)
      }
    }
    return toolDefinitions
  }

  /**
   * Get the list of tools for the assistant.
   */
  private static _getTools(agent: OpenAIAssistantAgent, kernel: Kernel): any[] {
    const tools: any[] = []

    for (const tool of (agent.definition as any).tools || []) {
      if ((tool as CodeInterpreterTool).type === 'code_interpreter') {
        tools.push({ type: 'code_interpreter' })
      } else if ((tool as FileSearchTool).type === 'file_search') {
        tools.push({ type: 'file_search' })
      }
    }

    const funcs = kernel.getFullListOfFunctionMetadata()
    tools.push(...funcs.map((f) => this._kernelFunctionMetadataToFunctionCallFormat(f as any)))

    return tools
  }

  /**
   * Convert kernel function metadata to OpenAI function call format.
   */
  private static _kernelFunctionMetadataToFunctionCallFormat(metadata: KernelFunctionMetadata): any {
    return {
      type: 'function',
      function: {
        name: metadata.fullyQualifiedName,
        description: metadata.description || '',
        parameters: {
          type: 'object',
          properties: Object.fromEntries(
            metadata.parameters.map((param) => [
              param.name,
              {
                type: (param as any).schema?.type || 'string',
                description: param.description || '',
              },
            ])
          ),
          required: metadata.parameters.filter((p) => p.isRequired).map((p) => p.name),
        },
      },
    }
  }

  // #region Content Generation Methods

  /**
   * Get message contents from ChatMessageContent.
   */
  private static _getMessageContents(message: ChatMessageContent): any[] {
    const contents: any[] = []

    if (message.content) {
      contents.push({ type: 'text', text: message.content })
    }

    for (const item of message.items) {
      if (item instanceof FileReferenceContent) {
        // Handle file reference content
        // Note: OpenAI API may need specific format for file references
        contents.push({ type: 'text', text: `[File: ${item.fileId}]` })
      }
    }

    return contents
  }

  /**
   * Generate function call content.
   */
  private static _generateFunctionCallContent(agentName: string, fccs: FunctionCallContent[]): ChatMessageContent {
    return new ChatMessageContent({
      role: AuthorRole.ASSISTANT,
      content: `Function calls: ${fccs.map((f) => f.functionName).join(', ')}`,
      name: agentName,
      items: fccs,
    })
  }

  /**
   * Generate streaming function call content.
   */
  private static _generateFunctionCallStreamingContent(
    agentName: string,
    fccs: FunctionCallContent[]
  ): StreamingChatMessageContent {
    return new StreamingChatMessageContent({
      role: AuthorRole.ASSISTANT,
      content: `Function calls: ${fccs.map((f) => f.functionName).join(', ')}`,
      name: agentName,
      choiceIndex: 0,
      items: fccs,
    })
  }

  /**
   * Generate code interpreter content.
   */
  private static _generateCodeInterpreterContent(agentName: string, input: string): ChatMessageContent {
    return new ChatMessageContent({
      role: AuthorRole.ASSISTANT,
      content: `Code interpreter: ${input}`,
      name: agentName,
    })
  }

  /**
   * Generate streaming code interpreter content.
   */
  private static _generateStreamingCodeInterpreterContent(
    agentName: string,
    stepDetails: any
  ): StreamingChatMessageContent {
    const input = stepDetails?.tool_calls?.[0]?.code_interpreter?.input || ''
    return new StreamingChatMessageContent({
      role: AuthorRole.ASSISTANT,
      content: `Code interpreter: ${input}`,
      name: agentName,
      choiceIndex: 0,
    })
  }

  /**
   * Generate function result content.
   */
  private static _generateFunctionResultContent(
    agentName: string,
    functionStep: FunctionCallContent,
    toolCall: any
  ): ChatMessageContent {
    const result = toolCall.function?.output || ''
    return new ChatMessageContent({
      role: AuthorRole.TOOL,
      content: result,
      name: agentName,
      items: [
        new FunctionResultContent({
          functionName: functionStep.functionName,
          pluginName: functionStep.pluginName,
          callId: functionStep.id,
          result,
        }),
      ],
    })
  }

  /**
   * Generate message content from OpenAI message.
   */
  private static _generateMessageContent(agentName: string, message: Message, step?: RunStep): ChatMessageContent {
    const textContents = message.content.filter((c) => c.type === 'text')
    const content = textContents.map((c: any) => c.text?.value || '').join('\n')

    return new ChatMessageContent({
      role: message.role === 'assistant' ? AuthorRole.ASSISTANT : AuthorRole.USER,
      content,
      name: agentName,
      metadata: {
        messageId: message.id,
        ...(step ? { stepId: step.id } : {}),
      },
    })
  }

  /**
   * Generate streaming message content.
   */
  private static _generateStreamingMessageContent(agentName: string, data: any): StreamingChatMessageContent {
    const delta = data.delta
    const content = delta?.content?.[0]?.text?.value || ''

    return new StreamingChatMessageContent({
      role: AuthorRole.ASSISTANT,
      content,
      name: agentName,
      choiceIndex: 0,
    })
  }

  /**
   * Generate final streaming message content.
   */
  private static _generateFinalStreamingMessageContent(
    agentName: string,
    message: Message,
    step: RunStep
  ): StreamingChatMessageContent {
    const textContents = message.content.filter((c) => c.type === 'text')
    const content = textContents.map((c: any) => c.text?.value || '').join('\n')

    return new StreamingChatMessageContent({
      role: message.role === 'assistant' ? AuthorRole.ASSISTANT : AuthorRole.USER,
      content,
      name: agentName,
      choiceIndex: 0,
      metadata: {
        messageId: message.id,
        stepId: step.id,
      },
    })
  }

  /**
   * Merge streaming function results.
   */
  private static _mergeStreamingFunctionResults(
    messages: ChatMessageContent[],
    agentName: string
  ): StreamingChatMessageContent {
    const results = messages
      .flatMap((m) => m.items)
      .filter((item) => item instanceof FunctionResultContent)
      .map((item) => (item as FunctionResultContent).result)
      .join('\n')

    return new StreamingChatMessageContent({
      role: AuthorRole.TOOL,
      content: results,
      name: agentName,
      choiceIndex: 0,
    })
  }

  /**
   * Get function call contents from a run.
   */
  private static _getFunctionCallContents(
    run: any,
    functionSteps: Map<string, FunctionCallContent>
  ): FunctionCallContent[] {
    const fccs: FunctionCallContent[] = []

    if (run.status === 'requires_action' && run.required_action?.type === 'submit_tool_outputs') {
      for (const toolCall of run.required_action.submit_tool_outputs.tool_calls) {
        if (toolCall.type === 'function') {
          const fcc = new FunctionCallContent({
            id: toolCall.id,
            functionName: toolCall.function.name,
            arguments: JSON.parse(toolCall.function.arguments || '{}'),
          })
          fccs.push(fcc)
          functionSteps.set(toolCall.id, fcc)
        }
      }
    }

    return fccs
  }

  // #endregion

  // #region Utility Methods

  /**
   * Sleep for the specified number of milliseconds.
   */
  private static _sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  /**
   * Execute a promise with a timeout.
   */
  private static async _withTimeout<T>(promise: Promise<T>, timeoutMs: number, errorMessage: string): Promise<T> {
    let timeoutHandle: NodeJS.Timeout

    const timeoutPromise = new Promise<never>((_, reject) => {
      timeoutHandle = setTimeout(() => reject(new Error(errorMessage)), timeoutMs)
    })

    try {
      return await Promise.race([promise, timeoutPromise])
    } finally {
      clearTimeout(timeoutHandle!)
    }
  }

  // #endregion
}
