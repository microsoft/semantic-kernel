import { FunctionResult } from '../../functions/function-result'
import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel, KernelFunction } from '../../kernel'
import { FilterContextBase } from '../filter-context-base'

/**
 * The context for function invocation filtering.
 *
 * This filter can be used to monitor which functions are called,
 * log what function was called with which parameters and what output,
 * and can be used for caching by setting the result value.
 */
export class FunctionInvocationContext extends FilterContextBase {
  /** The result of the function, or null if not yet executed */
  result?: FunctionResult | null

  constructor(options: {
    function: KernelFunction
    kernel: Kernel
    arguments: KernelArguments
    isStreaming?: boolean
    result?: FunctionResult | null
  }) {
    super(options)
    this.result = options.result ?? null
  }
}
