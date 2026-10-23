import type { KernelProcessStepState } from './kernel-process-step-state'

/**
 * A KernelProcessStep Base class for process steps.
 * @experimental
 */
export abstract class KernelProcessStep<TState = any> {
  state?: TState | null = null

  /**
   * Activates the step and sets the state.
   * @param state - The state to activate with
   */
  async activate(_state: KernelProcessStepState<TState>): Promise<void> {
    // Default implementation - subclasses may override
  }
}
