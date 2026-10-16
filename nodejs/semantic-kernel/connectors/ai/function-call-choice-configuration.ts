import { KernelFunctionMetadata } from '../../functions/kernel-function-metadata'

/**
 * Configuration for function call choice.
 *
 * @experimental This class is experimental and may change in the future.
 */
export class FunctionCallChoiceConfiguration {
  availableFunctions?: KernelFunctionMetadata[]

  constructor(options?: { availableFunctions?: KernelFunctionMetadata[] }) {
    this.availableFunctions = options?.availableFunctions
  }
}
