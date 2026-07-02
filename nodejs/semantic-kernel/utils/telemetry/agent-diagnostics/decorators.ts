import { Span, SpanStatusCode, trace } from '@opentelemetry/api'
import { Agent, AgentResponseItem } from '../../../agents/agent'
import { ChatMessageContent } from '../../../contents/chat-message-content'
import { StreamingChatMessageContent } from '../../../contents/streaming-chat-message-content'
import { AuthorRole } from '../../../contents/utils/author-role'
import { ModelDiagnosticSettings } from '../model-diagnostics/model-diagnostics-settings'
import * as genAiAttributes from './gen-ai-attributes'

/**
 * Module to instrument GenAI agents using OpenTelemetry and OpenTelemetry Semantic Conventions.
 * These are experimental features and may change in the future.
 *
 * To enable these features, set one of the following environment variables to true:
 *    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS
 *    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE
 * We are re-using the model diagnostic settings to control the instrumentation of agents
 * because it makes sense to have a system wide setting for diagnostics. The name "model"
 * is a legacy name because the concept of agent was not yet introduced when the settings were created.
 */

const MODEL_DIAGNOSTICS_SETTINGS = new ModelDiagnosticSettings()

// Creates a tracer from the global tracer provider
const tracer = trace.getTracer('semantic-kernel-agent-diagnostics')

const OPERATION_NAME = 'invoke_agent'

/**
 * Check if model diagnostics are enabled.
 *
 * Model diagnostics are enabled if either diagnostic is enabled or diagnostic with sensitive events is enabled.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function areModelDiagnosticsEnabled(): boolean {
  return MODEL_DIAGNOSTICS_SETTINGS.enableOtelDiagnostics || MODEL_DIAGNOSTICS_SETTINGS.enableOtelDiagnosticsSensitive
}

/**
 * Check if sensitive events are enabled.
 *
 * Sensitive events are enabled if the diagnostic with sensitive events is enabled.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function areSensitiveEventsEnabled(): boolean {
  return MODEL_DIAGNOSTICS_SETTINGS.enableOtelDiagnosticsSensitive
}

/**
 * Decorator to trace agent get response invocation.
 *
 * @example
 * ```typescript
 * class MyAgent extends Agent {
 *   @traceAgentGetResponse
 *   async getResponse(messages?: string | ChatMessageContent | Array<string | ChatMessageContent>): Promise<AgentResponseItem<ChatMessageContent>> {
 *     // Implementation
 *   }
 * }
 * ```
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function traceAgentGetResponse<T extends Agent>(
  _target: T,
  _propertyKey: string,
  descriptor: PropertyDescriptor
): PropertyDescriptor {
  const originalMethod = descriptor.value

  descriptor.value = async function (
    this: T,
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>,
    ...args: any[]
  ): Promise<AgentResponseItem<ChatMessageContent>> {
    if (!areModelDiagnosticsEnabled()) {
      // If model diagnostics are not enabled, just return the responses
      return await originalMethod.call(this, messages, ...args)
    }

    return await startAsCurrentSpan(this, async (span: Span) => {
      try {
        setAgentInvocationInput(span, messages)
        const response = await originalMethod.call(this, messages, ...args)
        setAgentInvocationOutput(span, [response.message])
        return response
      } catch (error) {
        setAgentInvocationError(span, error as Error)
        throw error
      }
    })
  }

  // Mark the wrapper as an agent diagnostics decorator
  ;(descriptor.value as any).__agent_diagnostics__ = true

  return descriptor
}

/**
 * Decorator to trace agent invocation (non-streaming).
 *
 * @example
 * ```typescript
 * class MyAgent extends Agent {
 *   @traceAgentInvocation
 *   async *invoke(messages?: string | ChatMessageContent | Array<string | ChatMessageContent>): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
 *     // Implementation
 *   }
 * }
 * ```
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function traceAgentInvocation<T extends Agent>(
  _target: T,
  _propertyKey: string,
  descriptor: PropertyDescriptor
): PropertyDescriptor {
  const originalMethod = descriptor.value

  descriptor.value = async function* (
    this: T,
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>,
    ...args: any[]
  ): AsyncIterable<AgentResponseItem<ChatMessageContent>> {
    if (!areModelDiagnosticsEnabled()) {
      // If model diagnostics are not enabled, just return the responses
      yield* originalMethod.call(this, messages, ...args)
      return
    }

    const span = await startSpan(this)
    setAgentInvocationInput(span, messages)
    try {
      const responses: ChatMessageContent[] = []
      for await (const response of originalMethod.call(this, messages, ...args)) {
        responses.push(response.message)
        yield response
      }
      setAgentInvocationOutput(span, responses)
    } catch (error) {
      setAgentInvocationError(span, error as Error)
      throw error
    } finally {
      span.end()
    }
  }

  // Mark the wrapper as an agent diagnostics decorator
  ;(descriptor.value as any).__agent_diagnostics__ = true

  return descriptor
}

/**
 * Decorator to trace agent streaming invocation.
 *
 * @example
 * ```typescript
 * class MyAgent extends Agent {
 *   @traceAgentStreamingInvocation
 *   async *invokeStreaming(messages?: string | ChatMessageContent | Array<string | ChatMessageContent>): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
 *     // Implementation
 *   }
 * }
 * ```
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function traceAgentStreamingInvocation<T extends Agent>(
  _target: T,
  _propertyKey: string,
  descriptor: PropertyDescriptor
): PropertyDescriptor {
  const originalMethod = descriptor.value

  descriptor.value = async function* (
    this: T,
    messages?: string | ChatMessageContent | Array<string | ChatMessageContent>,
    ...args: any[]
  ): AsyncIterable<AgentResponseItem<StreamingChatMessageContent>> {
    if (!areModelDiagnosticsEnabled()) {
      // If model diagnostics are not enabled, just return the responses
      yield* originalMethod.call(this, messages, ...args)
      return
    }

    const span = await startSpan(this)
    setAgentInvocationInput(span, messages)
    try {
      const chunks: StreamingChatMessageContent[] = []
      for await (const chunk of originalMethod.call(this, messages, ...args)) {
        chunks.push(chunk.message)
        yield chunk
      }
      // Concatenate the streaming chunks
      if (chunks.length > 0) {
        const response = chunks.reduce((acc, curr) => {
          // Concatenate content
          acc.content += curr.content
          // Merge items
          acc.items.push(...curr.items)
          // Merge metadata
          Object.assign(acc.metadata, curr.metadata)
          return acc
        })
        setAgentInvocationOutput(span, [response])
      } else {
        setAgentInvocationOutput(span, [])
      }
    } catch (error) {
      setAgentInvocationError(span, error as Error)
      throw error
    } finally {
      span.end()
    }
  }

  // Mark the wrapper as an agent diagnostics decorator
  ;(descriptor.value as any).__agent_diagnostics__ = true

  return descriptor
}

/**
 * Starts a span for the given agent and executes a function within it.
 *
 * @param agent - The agent for which to start the span.
 * @param fn - The function to execute within the span.
 * @returns The result of the function.
 */
async function startAsCurrentSpan<T>(agent: Agent, fn: (span: Span) => Promise<T>): Promise<T> {
  const attributes = getSpanAttributes(agent)

  return tracer.startActiveSpan(`${OPERATION_NAME} ${agent.name}`, { attributes }, async (span) => {
    try {
      return await fn(span)
    } finally {
      span.end()
    }
  })
}

/**
 * Starts a span for the given agent and returns it.
 * The caller is responsible for ending the span.
 *
 * @param agent - The agent for which to start the span.
 * @returns The started span.
 */
async function startSpan(agent: Agent): Promise<Span> {
  const attributes = getSpanAttributes(agent)
  return tracer.startSpan(`${OPERATION_NAME} ${agent.name}`, { attributes })
}

/**
 * Gets the span attributes for the given agent.
 *
 * @param agent - The agent for which to get attributes.
 * @returns The span attributes.
 */
function getSpanAttributes(agent: Agent): Record<string, any> {
  const attributes: Record<string, any> = {
    [genAiAttributes.OPERATION]: OPERATION_NAME,
    [genAiAttributes.AGENT_ID]: agent.id,
    [genAiAttributes.AGENT_NAME]: agent.name,
  }

  if (agent.description) {
    attributes[genAiAttributes.AGENT_DESCRIPTION] = agent.description
  }

  if (agent.kernel) {
    // This will only capture the tools that are available in the kernel at the time of agent creation.
    // If the agent is invoked with another kernel instance, the tools in that kernel will not be captured.
    const toolDefinitions = agent.kernel.getFullListOfFunctionMetadata().map((metadata) => ({
      name: metadata.name,
      pluginName: metadata.pluginName,
      description: metadata.description,
      parameters: metadata.parameters,
    }))
    if (toolDefinitions.length > 0) {
      attributes[genAiAttributes.AGENT_TOOL_DEFINITIONS] = JSON.stringify(toolDefinitions)
    }
  }

  return attributes
}

/**
 * Set the agent input attributes in the span.
 */
function setAgentInvocationInput(
  currentSpan: Span,
  messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
): void {
  if (areSensitiveEventsEnabled()) {
    const parsedMessages = parseAgentInvocationMessages(messages)
    currentSpan.setAttribute(
      genAiAttributes.AGENT_INVOCATION_INPUT,
      JSON.stringify(parsedMessages.map((message) => messageToDict(message)))
    )
  }
}

/**
 * Set the agent output attributes in the span.
 */
function setAgentInvocationOutput(currentSpan: Span, response: ChatMessageContent[]): void {
  if (areSensitiveEventsEnabled()) {
    currentSpan.setAttribute(
      genAiAttributes.AGENT_INVOCATION_OUTPUT,
      JSON.stringify(response.map((message) => messageToDict(message)))
    )
  }
}

/**
 * Set the agent error attributes in the span.
 */
function setAgentInvocationError(currentSpan: Span, error: Error): void {
  currentSpan.setAttribute(genAiAttributes.ERROR_TYPE, error.constructor.name)
  currentSpan.setStatus({ code: SpanStatusCode.ERROR, message: error.message })
}

/**
 * Parse the agent invocation messages into a list of ChatMessageContent.
 */
function parseAgentInvocationMessages(
  messages?: string | ChatMessageContent | Array<string | ChatMessageContent>
): ChatMessageContent[] {
  if (!messages) {
    return []
  }

  if (typeof messages === 'string') {
    return [new ChatMessageContent({ role: AuthorRole.USER, content: messages })]
  }

  if (messages instanceof ChatMessageContent) {
    return [messages]
  }

  if (Array.isArray(messages)) {
    return messages.map((msg) =>
      typeof msg === 'string' ? new ChatMessageContent({ role: AuthorRole.USER, content: msg }) : msg
    )
  }

  return []
}

/**
 * Convert a ChatMessageContent to a dictionary representation.
 */
function messageToDict(message: ChatMessageContent): Record<string, any> {
  return {
    role: message.role,
    content: message.content,
    name: message.name,
    metadata: message.metadata,
    items: message.items,
  }
}
