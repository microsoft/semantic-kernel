/**
 * The target of a function call in a kernel process.
 * @experimental
 */
export class KernelProcessFunctionTarget {
  /**
   * The step ID.
   */
  stepId: string

  /**
   * The function name.
   */
  functionName: string

  /**
   * The optional parameter name.
   */
  parameterName?: string | null = null

  /**
   * The optional target event ID.
   */
  targetEventId?: string | null = null

  constructor(params: {
    stepId: string
    functionName: string
    parameterName?: string | null
    targetEventId?: string | null
  }) {
    this.stepId = params.stepId
    this.functionName = params.functionName
    if (params.parameterName !== undefined) {
      this.parameterName = params.parameterName
    }
    if (params.targetEventId !== undefined) {
      this.targetEventId = params.targetEventId
    }
  }
}
