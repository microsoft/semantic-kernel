import { FilterContextBase } from './filter-context-base'
import { FilterTypes } from './filter-types'

/**
 * Error thrown when filter management operations fail.
 */
export class FilterManagementException extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'FilterManagementException'
  }
}

/**
 * Type for filter context.
 */
export type FilterContextType = FilterContextBase

/**
 * Type for callable filters.
 * Filters receive the context and a next function to call the next filter in the chain.
 */
export type CallableFilterType<T extends FilterContextType = FilterContextType> = (
  context: T,
  next: (context: T) => Promise<void>
) => Promise<void>

/**
 * Allowed filter types literal union.
 */
export type AllowedFiltersLiteral =
  | FilterTypes.AUTO_FUNCTION_INVOCATION
  | FilterTypes.FUNCTION_INVOCATION
  | FilterTypes.PROMPT_RENDERING

/**
 * Mapping from filter types to their property names.
 */
const FILTER_MAPPING: Record<FilterTypes, string> = {
  [FilterTypes.FUNCTION_INVOCATION]: 'functionInvocationFilters',
  [FilterTypes.PROMPT_RENDERING]: 'promptRenderingFilters',
  [FilterTypes.AUTO_FUNCTION_INVOCATION]: 'autoFunctionInvocationFilters',
}

/**
 * Base class for kernel filter extensions.
 */
export abstract class KernelFilterExtension {
  /** Function invocation filters */
  functionInvocationFilters: Array<[number, CallableFilterType]> = []

  /** Prompt rendering filters */
  promptRenderingFilters: Array<[number, CallableFilterType]> = []

  /** Auto function invocation filters */
  autoFunctionInvocationFilters: Array<[number, CallableFilterType]> = []

  /**
   * Add a filter to the Kernel.
   *
   * Each filter is added to the beginning of the list of filters.
   * Filters are executed in the order they are added, so the first filter added
   * will be the first to be executed, but it will also be the last executed
   * for the part after `await next(context)`.
   *
   * @param filterType - The type of the filter to add
   * @param filter - The filter function to add
   */
  addFilter(filterType: AllowedFiltersLiteral | FilterTypes, filter: CallableFilterType): void {
    try {
      // Ensure filterType is a FilterTypes enum value
      const type = typeof filterType === 'string' ? (filterType as FilterTypes) : filterType

      const filterListName = FILTER_MAPPING[type]
      const filterList = (this as any)[filterListName] as Array<[number, CallableFilterType]>

      // Use a unique ID for the filter (similar to Python's id())
      const filterId = this._generateFilterId(filter)
      filterList.unshift([filterId, filter])
    } catch (error) {
      throw new FilterManagementException(`Error adding filter ${filter} to ${filterType}: ${error}`)
    }
  }

  /**
   * Decorator to add a filter to the Kernel.
   *
   * @param filterType - The type of the filter
   * @returns A decorator function
   */
  filter(filterType: AllowedFiltersLiteral | FilterTypes): (func: CallableFilterType) => CallableFilterType {
    return (func: CallableFilterType): CallableFilterType => {
      this.addFilter(filterType, func)
      return func
    }
  }

  /**
   * Remove a filter from the Kernel.
   *
   * @param options - Options for removing the filter
   * @param options.filterType - The type of the filter to remove
   * @param options.filterId - The ID of the filter to remove
   * @param options.position - The position of the filter in the list
   */
  removeFilter(options: {
    filterType?: AllowedFiltersLiteral | FilterTypes
    filterId?: number
    position?: number
  }): void {
    const { filterType, filterId, position } = options

    if (filterId === undefined && position === undefined) {
      throw new FilterManagementException('Either filterId or position should be provided.')
    }

    // Ensure filterType is a FilterTypes enum value if provided
    const type = filterType && typeof filterType === 'string' ? (filterType as FilterTypes) : filterType

    // Remove by position
    if (position !== undefined) {
      if (!type) {
        throw new FilterManagementException('Please specify the type of filter when using position.')
      }
      const filterListName = FILTER_MAPPING[type]
      const filterList = (this as any)[filterListName] as Array<[number, CallableFilterType]>
      filterList.splice(position, 1)
      return
    }

    // Remove by filterId
    if (type) {
      const filterListName = FILTER_MAPPING[type]
      const filterList = (this as any)[filterListName] as Array<[number, CallableFilterType]>

      const index = filterList.findIndex(([fId]) => fId === filterId)
      if (index !== -1) {
        filterList.splice(index, 1)
        return
      }
    }

    // Search all filter lists
    for (const filterListName of Object.values(FILTER_MAPPING)) {
      const filterList = (this as any)[filterListName] as Array<[number, CallableFilterType]>
      const index = filterList.findIndex(([fId]) => fId === filterId)
      if (index !== -1) {
        filterList.splice(index, 1)
        return
      }
    }
  }

  /**
   * Construct the call stack for the given filter type.
   *
   * @param filterType - The type of filter
   * @param innerFunction - The inner function to execute at the end of the chain
   * @returns The constructed call stack function
   */
  constructCallStack<T extends FilterContextType>(
    filterType: FilterTypes,
    innerFunction: (context: T) => Promise<void>
  ): (context: T) => Promise<void> {
    const filterListName = FILTER_MAPPING[filterType]
    const filterList = (this as any)[filterListName] as Array<[number, CallableFilterType<T>]>

    // Build the call stack from innermost to outermost
    let stack: (context: T) => Promise<void> = innerFunction

    // Iterate through filters in order (they're already in reverse order due to unshift)
    for (const [, filter] of filterList) {
      const next = stack
      stack = (context: T) => filter(context, next)
    }

    return stack
  }

  /**
   * Generate a unique ID for a filter function.
   *
   * @param _filter - The filter function (not used, but kept for signature compatibility)
   * @returns A unique numeric ID
   */
  private _generateFilterId(_filter: CallableFilterType): number {
    // Use a simple counter-based approach
    // In a production system, you might want to use a more sophisticated ID generator
    if (!(this as any)._filterIdCounter) {
      ;(this as any)._filterIdCounter = 0
    }
    return ++(this as any)._filterIdCounter
  }
}
