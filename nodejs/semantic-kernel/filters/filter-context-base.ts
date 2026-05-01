import { Kernel, KernelFunction } from '../kernel'
import { KernelArguments } from '../functions/kernel-arguments'

/**
 * Base class for Kernel Filter Contexts.
 */
export abstract class FilterContextBase {
  /** The function being invoked */
  function: KernelFunction

  /** The kernel instance */
  kernel: Kernel

  /** The arguments passed to the function */
  arguments: KernelArguments

  /** Whether the function is streaming */
  isStreaming: boolean

  constructor(options: {
    function: KernelFunction
    kernel: Kernel
    arguments: KernelArguments
    isStreaming?: boolean
  }) {
    this.function = options.function
    this.kernel = options.kernel
    this.arguments = options.arguments
    this.isStreaming = options.isStreaming ?? false
  }
}
