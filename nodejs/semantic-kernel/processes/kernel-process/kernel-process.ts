import { kernelProcessToProcessStateMetadata } from '../process-state-metadata-utils'
import type { KernelProcessEdge } from './kernel-process-edge'
import { KernelProcessState } from './kernel-process-state'
import { KernelProcessStepInfo } from './kernel-process-step-info'
import type { KernelProcessStateMetadata } from './kernel-process-step-state-metadata'

/**
 * A kernel process.
 * @experimental
 */
export class KernelProcess extends KernelProcessStepInfo {
  /**
   * The steps in the process.
   */
  steps: KernelProcessStepInfo[] = []

  /**
   * The factories for creating steps with complex dependencies.
   */
  factories: Record<string, (...args: any[]) => any> = {}

  constructor(params: {
    state: KernelProcessState
    steps: KernelProcessStepInfo[]
    edges?: Record<string, KernelProcessEdge[]> | null
    factories?: Record<string, (...args: any[]) => any> | null
  }) {
    if (!params.state) {
      throw new Error('state cannot be null')
    }
    if (!params.steps || params.steps.length === 0) {
      throw new Error('steps cannot be null')
    }
    if (!params.state.name) {
      throw new Error('state.name cannot be null')
    }

    const processSteps = [...params.steps]

    super({
      innerStepType: KernelProcess,
      state: params.state,
      outputEdges: params.edges || {},
    })

    this.steps = processSteps

    if (params.factories) {
      this.factories = params.factories
    }
  }

  /**
   * Converts a kernel process to process state metadata.
   * @returns The process state metadata
   */
  toProcessStateMetadata(): KernelProcessStateMetadata {
    return kernelProcessToProcessStateMetadata(this)
  }
}
