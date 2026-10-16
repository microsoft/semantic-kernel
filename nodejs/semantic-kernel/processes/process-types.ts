import type { KernelProcessStep } from './kernel-process/kernel-process-step.js'

/**
 * Type variable for steps bound to KernelProcessStep.
 */
export type TStep = KernelProcessStep<any>

/**
 * Type variable for state.
 */
export type TState = any

/**
 * Given a subclass of KernelProcessStep, retrieve the concrete type of 'state'.
 * Note: TypeScript's runtime type information is limited, so this function
 * attempts to extract type information through reflection where possible.
 * @experimental
 * @param cls - The class to inspect
 * @returns The state type if it can be determined, otherwise null
 */
export function getGenericStateType(cls: new (...args: any[]) => any): any {
  try {
    // In TypeScript, we don't have runtime type information like Python's get_type_hints
    // This is a placeholder implementation. In practice, you might need to use
    // decorators or metadata to store type information at runtime, or rely on
    // explicit type parameters passed at construction time.

    // Check if the class has a static property that stores state type information
    // This would need to be set by a decorator or manually
    if ('__stateType__' in cls) {
      return (cls as any).__stateType__
    }

    // Recursively check base classes
    const proto = Object.getPrototypeOf(cls)
    if (proto && proto !== Function.prototype) {
      const baseType = getGenericStateType(proto)
      if (baseType !== null) {
        return baseType
      }
    }
  } catch {
    // Ignore errors
  }

  return null
}
