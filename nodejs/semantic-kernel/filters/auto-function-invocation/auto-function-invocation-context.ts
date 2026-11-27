import { PromptExecutionSettings } from '../../connectors/ai/prompt-execution-settings'
import { ChatHistory } from '../../contents/chat-history'
import { FunctionCallContent } from '../../contents/function-call-content'
import { FunctionResult } from '../../functions/function-result'
import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel, KernelFunction } from '../../kernel'
import { FilterContextBase } from '../filter-context-base'

/**
 * Options for constructing an AutoFunctionInvocationContext.
 */
export interface AutoFunctionInvocationContextOptions {
  /** The function being invoked */
  function: KernelFunction
  /** The kernel instance */
  kernel: Kernel
  /** The arguments passed to the function */
  arguments: KernelArguments
  /** Whether the function is streaming */
  isStreaming?: boolean
  /** The chat history or null */
  chatHistory?: ChatHistory | null
  /** The function call content or null */
  functionCallContent?: FunctionCallContent | null
  /** The function result or null */
  functionResult?: FunctionResult | null
  /** The execution settings or null */
  executionSettings?: PromptExecutionSettings | null
  /** The request sequence index */
  requestSequenceIndex?: number
  /** The function sequence index */
  functionSequenceIndex?: number
  /** The function count */
  functionCount?: number
  /** The flag to terminate */
  terminate?: boolean
}

/**
 * The context for auto function invocation filtering.
 *
 * This is the context supplied to the auto function invocation filters.
 *
 * Common use case are to alter the function_result, for instance filling it with a pre-computed
 * value, in order to skip a step, for instance when doing caching.
 *
 * Another option is to terminate, this can be done by setting terminate to true.
 */
export class AutoFunctionInvocationContext extends FilterContextBase {
  /** The chat history or null */
  chatHistory: ChatHistory | null = null

  /** The function call content or null */
  functionCallContent: FunctionCallContent | null = null

  /** The function result or null */
  functionResult: FunctionResult | null = null

  /** The execution settings or null */
  executionSettings: PromptExecutionSettings | null = null

  /** The request sequence index */
  requestSequenceIndex: number = 0

  /** The function sequence index */
  functionSequenceIndex: number = 0

  /** The function count */
  functionCount: number = 0

  /** The flag to terminate */
  terminate: boolean = false

  constructor(options: AutoFunctionInvocationContextOptions) {
    super({
      function: options.function,
      kernel: options.kernel,
      arguments: options.arguments,
      isStreaming: options.isStreaming,
    })

    this.chatHistory = options.chatHistory ?? null
    this.functionCallContent = options.functionCallContent ?? null
    this.functionResult = options.functionResult ?? null
    this.executionSettings = options.executionSettings ?? null
    this.requestSequenceIndex = options.requestSequenceIndex ?? 0
    this.functionSequenceIndex = options.functionSequenceIndex ?? 0
    this.functionCount = options.functionCount ?? 0
    this.terminate = options.terminate ?? false
  }
}
