/**
 * Metadata describing the version of the Step's implementation for serialization and replay.
 * @experimental
 */
export class KernelProcessStepMetadataAttribute {
  /**
   * The version string.
   */
  readonly version: string

  constructor(params: { version?: string } = {}) {
    this.version = params.version || 'v1'
  }
}

/**
 * Decorator to attach a version string representing the Step's implementation version.
 *
 * This version is serialized in `versionInfo` for each step, enabling replay
 * and process recovery to instantiate the correct Step variant.
 *
 * The version string used in @kernelProcessStepMetadata must uniquely identify the Step class'
 * behavior and contract version. Different versions imply incompatible step behavior, state schema,
 * or function/event definitions.
 *
 * @experimental
 * @param version - The version string (defaults to "v1")
 * @returns A class decorator
 *
 * @example
 * ```typescript
 * @kernelProcessStepMetadata("CutFoodStep.V2")
 * class CutFoodWithSharpeningStep extends KernelProcessStep<MyState> {
 *   // ...
 * }
 * ```
 */
export function kernelProcessStepMetadata(version: string = 'v1') {
  return function <T extends new (...args: any[]) => any>(constructor: T): T {
    ;(constructor as any)._kernel_process_step_metadata = new KernelProcessStepMetadataAttribute({ version })
    return constructor
  }
}
