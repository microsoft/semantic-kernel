// Classes in this file are shared between text search and vectors.
// They should not be imported directly, as they are also exposed in both modules.

import { KernelParameterMetadata } from '../functions/kernel-parameter-metadata'
import { createDefaultLogger, Logger } from '../utils/logger'

const logger: Logger = createDefaultLogger('SharedData')

export type TSearchResult = any
export type TSearchOptions = SearchOptions

/**
 * Default return parameter metadata for search functions.
 */
export const DEFAULT_RETURN_PARAMETER_METADATA: KernelParameterMetadata = new KernelParameterMetadata({
  name: 'results',
  description: 'The search results.',
  type: 'list[str]',
  typeObject: Array,
  isRequired: true,
})

/**
 * Default parameter metadata for search functions.
 */
export const DEFAULT_PARAMETER_METADATA: KernelParameterMetadata[] = [
  new KernelParameterMetadata({
    name: 'query',
    description: 'What to search for.',
    type: 'str',
    isRequired: true,
    typeObject: String,
  }),
  new KernelParameterMetadata({
    name: 'top',
    description: 'Number of results to return.',
    type: 'int',
    isRequired: false,
    defaultValue: 2,
    typeObject: Number,
  }),
  new KernelParameterMetadata({
    name: 'skip',
    description: 'Number of results to skip.',
    type: 'int',
    isRequired: false,
    defaultValue: 0,
    typeObject: Number,
  }),
]

/**
 * Default function name for search functions.
 */
export const DEFAULT_FUNCTION_NAME = 'search'

/**
 * Options for a search.
 *
 * When multiple filters are used, they are combined with an AND operator.
 * @releaseCandidate
 */
export class SearchOptions {
  filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null =
    null
  skip: number = 0
  top: number = 5
  includeTotalCount: boolean = false

  constructor(params?: {
    filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
    skip?: number
    top?: number
    includeTotalCount?: boolean
    [key: string]: any
  }) {
    if (params) {
      if (params.filter !== undefined) {
        this.filter = params.filter
      }
      if (params.skip !== undefined) {
        if (params.skip < 0) {
          throw new Error('skip must be >= 0')
        }
        this.skip = params.skip
      }
      if (params.top !== undefined) {
        if (params.top <= 0) {
          throw new Error('top must be > 0')
        }
        this.top = params.top
      }
      if (params.includeTotalCount !== undefined) {
        this.includeTotalCount = params.includeTotalCount
      }

      // Allow extra properties to be set
      for (const [key, value] of Object.entries(params)) {
        if (key !== 'filter' && key !== 'skip' && key !== 'top' && key !== 'includeTotalCount') {
          ;(this as any)[key] = value
        }
      }
    }
  }

  /**
   * Convert the options to a plain object.
   */
  toObject(): Record<string, any> {
    const obj: Record<string, any> = {}
    for (const [key, value] of Object.entries(this)) {
      if (value !== null && value !== undefined) {
        obj[key] = value
      }
    }
    return obj
  }
}

/**
 * The result of a kernel search.
 * @releaseCandidate
 */
export class KernelSearchResults<TSearchResult = any> {
  results: AsyncIterable<TSearchResult>
  totalCount?: number | null = null
  metadata?: Record<string, any> | null = null

  constructor(params: {
    results: AsyncIterable<TSearchResult>
    totalCount?: number | null
    metadata?: Record<string, any> | null
  }) {
    this.results = params.results
    if (params.totalCount !== undefined) {
      this.totalCount = params.totalCount
    }
    if (params.metadata !== undefined) {
      this.metadata = params.metadata
    }
  }
}

/**
 * Type definition for the filter update function in Text Search.
 */
export type DynamicFilterFunction = (params: {
  filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
  parameters?: KernelParameterMetadata[] | null
  [key: string]: any
}) => string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null

/**
 * Create search options.
 *
 * If options are supplied, they are checked for the right type, and the kwargs are used to update the options.
 *
 * If options are not supplied, they are created from the kwargs.
 * If that fails, an empty options object is returned.
 *
 * @param optionsClass - The class of the options
 * @param options - The existing options to update
 * @param kwargs - The keyword arguments to use to create the options
 * @returns The options of type optionsClass
 */
export function createOptions<T extends SearchOptions>(
  optionsClass: new (params?: any) => T,
  options: SearchOptions | null,
  kwargs?: Record<string, any>
): T {
  const kw = kwargs || {}

  // No options given, so just try to create from kwargs
  if (!options) {
    return new optionsClass(kw)
  }

  // Options are the right class, just update based on kwargs
  if (!(options instanceof optionsClass)) {
    // Options are not the right class, so create new options
    const additionalKwargs: Record<string, any> = {}
    try {
      Object.assign(additionalKwargs, options.toObject())
    } catch {
      // This is very unlikely to happen, but if it does, we will just create new options
      logger.warn('Options are not valid. Creating new options from just kwargs.')
    }
    Object.assign(kw, additionalKwargs)
    return new optionsClass(kw)
  }

  // Update existing options with kwargs
  for (const [key, value] of Object.entries(kw)) {
    ;(options as any)[key] = value
  }

  return options as T
}

/**
 * The default options update function.
 *
 * This function is used to update the query and options with the kwargs.
 * You can supply your own version of this function to customize the behavior.
 *
 * @param params - The parameters
 * @param params.filter - The filter to use for the search
 * @param params.parameters - The parameters to use to create the options
 * @param params.kwargs - The keyword arguments to use to update the options
 * @returns The updated filters
 */
export function defaultDynamicFilterFunction(params: {
  filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
  parameters?: KernelParameterMetadata[] | null
  [key: string]: any
}): string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null {
  const { filter = null, parameters, ...kwargs } = params
  let updatedFilter = filter

  for (const param of parameters || []) {
    if (!param.name) continue

    if (['query', 'top', 'skip', 'include_total_count'].includes(param.name)) {
      continue
    }

    let newFilter: string | null = null

    if (param.name in kwargs) {
      newFilter = `lambda x: x.${param.name} == '${kwargs[param.name]}'`
    } else if (param.defaultValue) {
      newFilter = `lambda x: x.${param.name} == '${param.defaultValue}'`
    }

    if (!newFilter) {
      continue
    }

    if (updatedFilter === null || updatedFilter === undefined) {
      updatedFilter = newFilter
    } else if (Array.isArray(updatedFilter)) {
      updatedFilter.push(newFilter)
    } else {
      updatedFilter = [updatedFilter, newFilter]
    }
  }

  return updatedFilter
}
