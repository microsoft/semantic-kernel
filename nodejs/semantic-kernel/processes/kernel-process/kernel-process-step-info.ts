import type { KernelProcessEdge } from './kernel-process-edge'
import type { KernelProcessStepState } from './kernel-process-step-state'

/**
 * Information about a step in a kernel process.
 * @experimental
 */
export class KernelProcessStepInfo {
  /**
   * The inner step type (constructor/class).
   */
  innerStepType: new (...args: any[]) => any

  /**
   * The state of the step.
   */
  state: KernelProcessStepState

  /**
   * The output edges for this step.
   */
  outputEdges: Record<string, KernelProcessEdge[]>

  constructor(params: {
    innerStepType: new (...args: any[]) => any
    state: KernelProcessStepState
    outputEdges: Record<string, KernelProcessEdge[]>
  }) {
    this.innerStepType = params.innerStepType
    this.state = params.state
    this.outputEdges = params.outputEdges
  }

  /**
   * Gets a copy of the edges of the step.
   */
  get edges(): Record<string, KernelProcessEdge[]> {
    return Object.fromEntries(Object.entries(this.outputEdges).map(([k, v]) => [k, [...v]]))
  }
}
