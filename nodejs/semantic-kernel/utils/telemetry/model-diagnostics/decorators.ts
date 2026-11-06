import { context, Span, SpanStatusCode, trace } from '@opentelemetry/api'
import { ChatCompletionClientBase } from '../../../connectors/ai/chat-completion-client-base'
import { CompletionUsage } from '../../../connectors/ai/completion-usage'
import { PromptExecutionSettings } from '../../../connectors/ai/prompt-execution-settings'
import { ChatHistory } from '../../../contents/chat-history'
import { ChatMessageContent } from '../../../contents/chat-message-content'
import { StreamingChatMessageContent } from '../../../contents/streaming-chat-message-content'
import { StreamingTextContent } from '../../../contents/streaming-text-content'
import { TextContent } from '../../../contents/text-content'
import { createDefaultLogger } from '../../logger'
import * as genAiAttributes from './gen-ai-attributes'
import { ModelDiagnosticSettings } from './model-diagnostics-settings'

const logger = createDefaultLogger('ModelDiagnosticsDecorators')

/**
 * Module to instrument GenAI models using OpenTelemetry and OpenTelemetry Semantic Conventions.
 * These are experimental features and may change in the future.
 *
 * To enable these features, set one of the following environment variables to true:
 *    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS
 *    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE
 */

const MODEL_DIAGNOSTICS_SETTINGS = new ModelDiagnosticSettings()

// Operation names
const CHAT_COMPLETION_OPERATION = 'chat'
const TEXT_COMPLETION_OPERATION = 'text_completions'

// Creates a tracer from the global tracer provider
const tracer = trace.getTracer(__filename)

/**
 * Check if model diagnostics are enabled.
 *
 * Model diagnostics are enabled if either diagnostic is enabled or diagnostic with sensitive events is enabled.
 */
export function areModelDiagnosticsEnabled(): boolean {
  return MODEL_DIAGNOSTICS_SETTINGS.enableOtelDiagnostics || MODEL_DIAGNOSTICS_SETTINGS.enableOtelDiagnosticsSensitive
}

/**
 * Check if sensitive events are enabled.
 *
 * Sensitive events are enabled if the diagnostic with sensitive events is enabled.
 */
export function areSensitiveEventsEnabled(): boolean {
  return MODEL_DIAGNOSTICS_SETTINGS.enableOtelDiagnosticsSensitive
}

/**
 * Decorator to trace chat completion activities.
 *
 * @param modelProvider - The model provider should describe a family of
 *   GenAI models with specific model identified by ai_model_id. For example,
 *   model_provider could be "openai" and ai_model_id could be "gpt-3.5-turbo".
 *   Sometimes the model provider is unknown at runtime, in which case it can be
 *   set to the most specific known provider. For example, while using local models
 *   hosted by Ollama, the model provider could be set to "ollama".
 */
export function traceChatCompletion(modelProvider: string) {
  return function <T extends ChatCompletionClientBase>(
    _target: T,
    _propertyKey: string,
    descriptor: PropertyDescriptor
  ): PropertyDescriptor {
    const originalMethod = descriptor.value

    descriptor.value = async function (
      this: T,
      chatHistory: ChatHistory,
      settings: PromptExecutionSettings,
      ...args: any[]
    ): Promise<ChatMessageContent[]> {
      if (!areModelDiagnosticsEnabled()) {
        return await originalMethod.call(this, chatHistory, settings, ...args)
      }

      const span = getCompletionSpan(
        CHAT_COMPLETION_OPERATION,
        this.aiModelId,
        modelProvider,
        this.serviceUrl?.() ?? null,
        settings
      )

      return await context.with(trace.setSpan(context.active(), span), async () => {
        try {
          setCompletionInput(modelProvider, chatHistory)
          const completions = await originalMethod.call(this, chatHistory, settings, ...args)
          setCompletionResponse(span, completions, modelProvider)
          return completions
        } catch (error) {
          setCompletionError(span, error as Error)
          throw error
        } finally {
          span.end()
        }
      })
    }

    // Mark the wrapper as a chat completion decorator
    ;(descriptor.value as any).__modelDiagnosticsChatCompletion__ = true

    return descriptor
  }
}

/**
 * Decorator to trace streaming chat completion activities.
 *
 * @param modelProvider - The model provider should describe a family of
 *   GenAI models with specific model identified by ai_model_id.
 */
export function traceStreamingChatCompletion(modelProvider: string) {
  return function <T extends ChatCompletionClientBase>(
    _target: T,
    _propertyKey: string,
    descriptor: PropertyDescriptor
  ): PropertyDescriptor {
    const originalMethod = descriptor.value

    descriptor.value = async function* (
      this: T,
      chatHistory: ChatHistory,
      settings: PromptExecutionSettings,
      ...args: any[]
    ): AsyncGenerator<StreamingChatMessageContent[], void, unknown> {
      if (!areModelDiagnosticsEnabled()) {
        yield* originalMethod.call(this, chatHistory, settings, ...args)
        return
      }

      const allMessages: Map<number, StreamingChatMessageContent[]> = new Map()
      const span = getCompletionSpan(
        CHAT_COMPLETION_OPERATION,
        this.aiModelId,
        modelProvider,
        this.serviceUrl?.() ?? null,
        settings
      )

      try {
        setCompletionInput(modelProvider, chatHistory)

        for await (const streamingChatMessageContents of originalMethod.call(this, chatHistory, settings, ...args)) {
          for (const streamingChatMessageContent of streamingChatMessageContents) {
            const choiceIndex = streamingChatMessageContent.choiceIndex
            if (!allMessages.has(choiceIndex)) {
              allMessages.set(choiceIndex, [])
            }
            allMessages.get(choiceIndex)!.push(streamingChatMessageContent)
          }
          yield streamingChatMessageContents
        }

        // Merge all messages
        const allMessagesFlattened: StreamingChatMessageContent[] = Array.from(allMessages.values()).map((messages) =>
          messages.reduce((x, y) => (x as any).add(y) as StreamingChatMessageContent)
        )
        setCompletionResponse(span, allMessagesFlattened, modelProvider)
      } catch (error) {
        setCompletionError(span, error as Error)
        throw error
      } finally {
        span.end()
      }
    }

    // Mark the wrapper as a streaming chat completion decorator
    ;(descriptor.value as any).__modelDiagnosticsStreamingChatCompletion__ = true

    return descriptor
  }
}

/**
 * Decorator to trace text completion activities.
 *
 * @param modelProvider - The model provider should describe a family of
 *   GenAI models with specific model identified by ai_model_id.
 */
export function traceTextCompletion(modelProvider: string) {
  return function <T>(_target: T, _propertyKey: string, descriptor: PropertyDescriptor): PropertyDescriptor {
    const originalMethod = descriptor.value

    descriptor.value = async function (
      this: T,
      prompt: string,
      settings: PromptExecutionSettings,
      ...args: any[]
    ): Promise<TextContent[]> {
      if (!areModelDiagnosticsEnabled()) {
        return await originalMethod.call(this, prompt, settings, ...args)
      }

      const completionService = this as any
      const span = getCompletionSpan(
        TEXT_COMPLETION_OPERATION,
        completionService.aiModelId,
        modelProvider,
        completionService.serviceUrl?.() ?? null,
        settings
      )

      return await context.with(trace.setSpan(context.active(), span), async () => {
        try {
          setCompletionInput(modelProvider, prompt)
          const completions = await originalMethod.call(this, prompt, settings, ...args)
          setCompletionResponse(span, completions, modelProvider)
          return completions
        } catch (error) {
          setCompletionError(span, error as Error)
          throw error
        } finally {
          span.end()
        }
      })
    }

    // Mark the wrapper as a text completion decorator
    ;(descriptor.value as any).__modelDiagnosticsTextCompletion__ = true

    return descriptor
  }
}

/**
 * Decorator to trace streaming text completion activities.
 *
 * @param modelProvider - The model provider should describe a family of
 *   GenAI models with specific model identified by ai_model_id.
 */
export function traceStreamingTextCompletion(modelProvider: string) {
  return function <T>(_target: T, _propertyKey: string, descriptor: PropertyDescriptor): PropertyDescriptor {
    const originalMethod = descriptor.value

    descriptor.value = async function* (
      this: T,
      prompt: string,
      settings: PromptExecutionSettings,
      ...args: any[]
    ): AsyncGenerator<StreamingTextContent[], void, unknown> {
      if (!areModelDiagnosticsEnabled()) {
        yield* originalMethod.call(this, prompt, settings, ...args)
        return
      }

      const completionService = this as any
      const allTextContents: Map<number, StreamingTextContent[]> = new Map()
      const span = getCompletionSpan(
        TEXT_COMPLETION_OPERATION,
        completionService.aiModelId,
        modelProvider,
        completionService.serviceUrl?.() ?? null,
        settings
      )

      try {
        setCompletionInput(modelProvider, prompt)

        for await (const streamingTextContents of originalMethod.call(this, prompt, settings, ...args)) {
          for (const streamingTextContent of streamingTextContents) {
            const choiceIndex = streamingTextContent.choiceIndex
            if (!allTextContents.has(choiceIndex)) {
              allTextContents.set(choiceIndex, [])
            }
            allTextContents.get(choiceIndex)!.push(streamingTextContent)
          }
          yield streamingTextContents
        }

        // Merge all text contents
        const allTextContentsFlattened: StreamingTextContent[] = Array.from(allTextContents.values()).map((messages) =>
          messages.reduce((x, y) => (x as any).add(y) as StreamingTextContent)
        )
        setCompletionResponse(span, allTextContentsFlattened, modelProvider)
      } catch (error) {
        setCompletionError(span, error as Error)
        throw error
      } finally {
        span.end()
      }
    }

    // Mark the wrapper as a streaming text completion decorator
    ;(descriptor.value as any).__modelDiagnosticsStreamingTextCompletion__ = true

    return descriptor
  }
}

/**
 * Start a text or chat completion span for a given model.
 *
 * Note that `startSpan` doesn't make the span the current span.
 * Use context.with() to make it the current span.
 */
function getCompletionSpan(
  operationName: string,
  modelName: string,
  modelProvider: string,
  serviceUrl: string | null,
  executionSettings: PromptExecutionSettings | null
): Span {
  const span = tracer.startSpan(`${operationName} ${modelName}`)

  // Set attributes on the span
  span.setAttributes({
    [genAiAttributes.OPERATION]: operationName,
    [genAiAttributes.SYSTEM]: modelProvider,
    [genAiAttributes.MODEL]: modelName,
  })

  if (serviceUrl) {
    span.setAttribute(genAiAttributes.ADDRESS, serviceUrl)
  }

  // Set execution settings attributes
  if (executionSettings) {
    const attributeNameMap: Record<string, string> = {
      seed: genAiAttributes.SEED,
      encodingFormats: genAiAttributes.ENCODING_FORMATS,
      frequencyPenalty: genAiAttributes.FREQUENCY_PENALTY,
      maxTokens: genAiAttributes.MAX_TOKENS,
      stopSequences: genAiAttributes.STOP_SEQUENCES,
      temperature: genAiAttributes.TEMPERATURE,
      topK: genAiAttributes.TOP_K,
      topP: genAiAttributes.TOP_P,
    }

    for (const [attributeName, attributeKey] of Object.entries(attributeNameMap)) {
      const attribute = (executionSettings as any).extensionData?.[attributeName]
      if (attribute !== undefined) {
        span.setAttribute(attributeKey, attribute)
      }
    }
  }

  return span
}

/**
 * Set the input for a text or chat completion.
 *
 * The logs will be associated to the current span.
 */
function setCompletionInput(modelProvider: string, prompt: string | ChatHistory): void {
  if (areSensitiveEventsEnabled()) {
    if (typeof prompt !== 'string' && 'messages' in prompt) {
      // ChatHistory
      const chatHistory = prompt as ChatHistory
      for (let idx = 0; idx < chatHistory.messages.length; idx++) {
        const message = chatHistory.messages[idx]
        const eventName = genAiAttributes.ROLE_EVENT_MAP[message.role]
        if (eventName) {
          logger.info(JSON.stringify(message.toDict()), {
            [genAiAttributes.EVENT_NAME]: eventName,
            [genAiAttributes.SYSTEM]: modelProvider,
            CHAT_MESSAGE_INDEX: idx,
          })
        }
      }
    } else {
      // String prompt
      logger.info(prompt, {
        [genAiAttributes.EVENT_NAME]: genAiAttributes.PROMPT,
        [genAiAttributes.SYSTEM]: modelProvider,
      })
    }
  }
}

/**
 * Set the a text or chat completion response for a given span.
 */
function setCompletionResponse(
  currentSpan: Span,
  completions: ChatMessageContent[] | TextContent[] | StreamingChatMessageContent[] | StreamingTextContent[],
  modelProvider: string
): void {
  if (completions.length === 0) {
    return
  }

  const firstCompletion = completions[0]

  // Set the response ID
  const responseId = firstCompletion.metadata?.id
  if (responseId) {
    currentSpan.setAttribute(genAiAttributes.RESPONSE_ID, responseId)
  }

  // Set the finish reason
  const finishReasons = completions
    .filter((c): c is ChatMessageContent => 'finishReason' in c)
    .map((c) => String(c.finishReason))
    .filter(Boolean)
  if (finishReasons.length > 0) {
    currentSpan.setAttribute(genAiAttributes.FINISH_REASON, finishReasons.join(','))
  }

  // Set usage attributes
  const usage = firstCompletion.metadata?.usage as CompletionUsage | undefined
  if (usage) {
    if (usage.promptTokens !== undefined) {
      currentSpan.setAttribute(genAiAttributes.INPUT_TOKENS, usage.promptTokens)
    }
    if (usage.completionTokens !== undefined) {
      currentSpan.setAttribute(genAiAttributes.OUTPUT_TOKENS, usage.completionTokens)
    }
  }

  // Set the completion event
  if (areSensitiveEventsEnabled()) {
    for (const completion of completions) {
      const fullResponse: any = {
        message: completion.toDict(),
      }

      if ('finishReason' in completion) {
        fullResponse.finish_reason = (completion as ChatMessageContent).finishReason
      }
      if ('choiceIndex' in completion) {
        fullResponse.index = (completion as any).choiceIndex
      }

      logger.info(JSON.stringify(fullResponse), {
        [genAiAttributes.EVENT_NAME]: genAiAttributes.CHOICE,
        [genAiAttributes.SYSTEM]: modelProvider,
      })
    }
  }
}

/**
 * Set an error for a text or chat completion.
 */
function setCompletionError(span: Span, error: Error): void {
  span.setAttribute(genAiAttributes.ERROR_TYPE, error.constructor.name)
  span.setStatus({
    code: SpanStatusCode.ERROR,
    message: String(error),
  })
}
