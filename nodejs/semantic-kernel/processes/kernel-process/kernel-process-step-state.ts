/**
 * The state of a step in a kernel process.
 * @experimental
 */
export class KernelProcessStepState<TState = any> {
  /**
   * The type identifier for this state.
   */
  type: 'KernelProcessStepState' | 'KernelProcessState' = 'KernelProcessStepState'

  /**
   * The name of the step.
   */
  name: string

  /**
   * The version of the step.
   */
  version: string

  /**
   * The optional ID of the step.
   */
  id?: string | null = null

  /**
   * The state data.
   */
  state?: TState | null = null

  constructor(params: { name: string; version: string; id?: string | null; state?: TState | null }) {
    this.name = params.name
    this.version = params.version
    if (params.id !== undefined) {
      this.id = params.id
    }
    if (params.state !== undefined) {
      this.state = params.state
    }
  }
}
