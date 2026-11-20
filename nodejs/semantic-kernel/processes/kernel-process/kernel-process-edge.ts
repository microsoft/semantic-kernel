import type { KernelProcessFunctionTarget } from './kernel-process-function-target'

/**
 * Represents an edge between steps.
 * @experimental
 */
export class KernelProcessEdge {
  /**
   * The source step ID.
   */
  sourceStepId: string

  /**
   * The output target for this edge.
   */
  outputTarget: KernelProcessFunctionTarget

  constructor(params: { sourceStepId: string; outputTarget: KernelProcessFunctionTarget }) {
    this.sourceStepId = params.sourceStepId
    this.outputTarget = params.outputTarget
  }
}
