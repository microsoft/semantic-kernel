import { KernelProcessStepState } from './kernel-process-step-state'

/**
 * The state of a kernel process.
 * @experimental
 */
export class KernelProcessState<TState = any> extends KernelProcessStepState<TState> {
  /**
   * The type identifier for this state.
   */
  override type = 'KernelProcessState' as const

  constructor(params: { name: string; version: string; id?: string | null; state?: TState | null }) {
    super(params)
    this.type = 'KernelProcessState'
  }
}
