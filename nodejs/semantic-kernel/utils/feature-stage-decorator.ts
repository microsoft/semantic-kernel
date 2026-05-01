/**
 * Version constant - should match the package version
 */
const VERSION = '0.0.1'

/**
 * Default release candidate version
 */
export const DEFAULT_RC_VERSION = `${VERSION}-rc9`

/**
 * Default release candidate note
 */
const DEFAULT_RC_NOTE =
  'Features marked with this status are nearing completion and are considered ' +
  'stable for most purposes, but may still incur minor refinements or ' +
  'optimizations before achieving full general availability.'

/**
 * Type representing a class constructor or a function
 */
// eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
type DecoratorTarget = Function | (new (...args: any[]) => any)

/**
 * Metadata interface for stage information
 */
interface StageMetadata {
  stage_status?: string
  stage_version?: string
  is_experimental?: boolean
  is_release_candidate?: boolean
}

/**
 * Appends or sets the docstring-like comment for the given target.
 * In TypeScript, we store this as a property since we don't have Python-style docstrings.
 * @param target - The function or class to update
 * @param note - The note to append
 */
function updateDocstring(target: DecoratorTarget & { __doc__?: string }, note: string): void {
  if (target.__doc__) {
    target.__doc__ += `\n\n${note}`
  } else {
    target.__doc__ = note
  }
}

/**
 * A general-purpose decorator for marking a function or a class.
 *
 * It updates the docstring and attaches 'stage_status' (and optionally
 * 'stage_version') as metadata. A custom 'note' may be provided to
 * override the default appended text.
 *
 * @example
 * ```typescript
 * @stage({ status: "experimental" })
 * class MyExperimentalClass {
 *   // A class that is still evolving rapidly.
 * }
 *
 * @stage({ status: "experimental", version: "0.1.0" })
 * function myExperimentalFunction() {
 *   // A function that is still evolving rapidly.
 * }
 * ```
 *
 * @param options - Configuration options
 * @param options.status - The development stage (e.g., 'experimental', 'release_candidate', etc.)
 * @param options.version - Optional version or release info (e.g., '1.21.0-rc4')
 * @param options.note - A custom note to append to the docstring
 * @returns A decorator that updates the docstring and metadata of the target
 */
export function stage(
  options: {
    status?: string
    version?: string
    note?: string
  } = {}
): <T extends DecoratorTarget>(target: T) => T {
  const { status = 'experimental', version, note } = options

  return function <T extends DecoratorTarget>(target: T): T {
    const entityType = typeof target === 'function' && target.prototype ? 'class' : 'function'
    const verText = version ? ` (Version: ${version})` : ''
    const defaultNote = `Note: This ${entityType} is marked as '${status}'${verText} and may change in the future.`
    const finalNote = note ?? defaultNote

    updateDocstring(target as any, finalNote)

    const metadata = target as T & StageMetadata
    metadata.stage_status = status
    if (version) {
      metadata.stage_version = version
    }

    return target
  }
}

/**
 * Decorator specifically for 'experimental' features.
 *
 * It uses the general 'stage' decorator but also attaches
 * 'is_experimental = true'.
 *
 * @example
 * ```typescript
 * @experimental
 * class MyExperimentalClass {
 *   // A class that is still evolving rapidly.
 * }
 *
 * @experimental
 * function myExperimentalFunction() {
 *   // A function that is still evolving rapidly.
 * }
 * ```
 *
 * @param target - The function or class to decorate
 * @returns The decorated target with experimental metadata
 */
export function experimental<T extends DecoratorTarget>(target: T): T {
  const decorated = stage({ status: 'experimental' })(target)
  const metadata = decorated as T & StageMetadata
  metadata.is_experimental = true
  return decorated
}

/**
 * Decorator that designates a function/class as being in a 'release candidate' state.
 *
 * By default, applies a descriptive note indicating near-completion and possible minor refinements
 * before achieving general availability. You may override this with a custom 'docString' if needed.
 *
 * @example
 * ```typescript
 * // Usage 1: Simple decorator
 * @releaseCandidate
 * class MyRCClass {
 *   // A class that is nearly final, but still in release-candidate stage.
 * }
 *
 * // Usage 2: With version string
 * @releaseCandidate("1.21.3-rc1")
 * class MyRCClass2 {
 *   // A class with a specific RC version.
 * }
 *
 * // Usage 3: With options object
 * @releaseCandidate({ version: "1.21.3-rc1" })
 * class MyRCClass3 {
 *   // A class with version specified via options.
 * }
 *
 * // Usage 4: With custom doc string
 * @releaseCandidate({ docString: "Custom RC note..." })
 * class MyRCClass4 {
 *   // A class with custom documentation.
 * }
 * ```
 *
 * @param targetOrVersion - Either the target being decorated, a version string, or options object
 * @returns The decorated target or a decorator function
 */
export function releaseCandidate<T extends DecoratorTarget>(
  targetOrVersion?: T | string | { version?: string; docString?: string }
): T | ((target: T) => T) {
  function apply(target: T, ver: string, note?: string): T {
    const verText = ver ? ` (Version: ${ver})` : ''
    const rcNote = note !== undefined ? note : `${DEFAULT_RC_NOTE}${verText}`

    const decorated = stage({
      status: 'release_candidate',
      version: ver,
      note: rcNote,
    })(target)

    const metadata = decorated as T & StageMetadata
    metadata.is_release_candidate = true
    return decorated
  }

  // Case 1: Used as @releaseCandidate (no arguments)
  if (typeof targetOrVersion === 'function') {
    return apply(targetOrVersion, DEFAULT_RC_VERSION, undefined)
  }

  // Case 2: Used as @releaseCandidate("version-string")
  if (typeof targetOrVersion === 'string') {
    return function (target: T): T {
      return apply(target, targetOrVersion, undefined)
    }
  }

  // Case 3: Used as @releaseCandidate({ version, docString })
  if (typeof targetOrVersion === 'object' && targetOrVersion !== null) {
    const { version, docString } = targetOrVersion
    return function (target: T): T {
      return apply(target, version || DEFAULT_RC_VERSION, docString)
    }
  }

  // Case 4: Used as @releaseCandidate() (called with no arguments)
  return function (target: T): T {
    return apply(target, DEFAULT_RC_VERSION, undefined)
  }
}

/**
 * Example usage:
 *
 * ```typescript
 * @experimental
 * class MyExperimentalClass {
 *   // A class that is still evolving rapidly.
 * }
 *
 * @stage({ status: "experimental" })
 * class MyExperimentalClass2 {
 *   // A class that is still evolving rapidly.
 * }
 *
 * @experimental
 * function myExperimentalFunction() {
 *   // A function that is still evolving rapidly.
 * }
 *
 * @releaseCandidate
 * class MyRCClass {
 *   // A class that is nearly final, but still in release-candidate stage.
 * }
 *
 * @releaseCandidate("1.23.1-rc1")
 * class MyRCClass2 {
 *   // A class that is nearly final, but still in release-candidate stage.
 * }
 * ```
 */
