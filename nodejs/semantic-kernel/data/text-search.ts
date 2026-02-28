import { TextSearchException } from '../exceptions/search-exceptions'
import type { KernelFunction } from '../functions/kernel-function'
import { KernelFunctionFromMethod } from '../functions/kernel-function-from-method'
import type { KernelParameterMetadata } from '../functions/kernel-parameter-metadata'
import { createDefaultLogger } from '../utils/logger'
import {
  DEFAULT_FUNCTION_NAME,
  DEFAULT_PARAMETER_METADATA,
  DEFAULT_RETURN_PARAMETER_METADATA,
  type DynamicFilterFunction,
  type KernelSearchResults,
  SearchOptions,
  createOptions,
  defaultDynamicFilterFunction,
} from './_shared'

const logger = createDefaultLogger('TextSearch')

/**
 * The default description for search functions.
 */
export const DEFAULT_DESCRIPTION =
  'Perform a search for content related to the specified query and return string results'

/**
 * The result of a text search.
 * @releaseCandidate
 */
export class TextSearchResult {
  name?: string | null = null
  value?: string | null = null
  link?: string | null = null

  constructor(params?: { name?: string | null; value?: string | null; link?: string | null }) {
    if (params) {
      this.name = params.name
      this.value = params.value
      this.link = params.link
    }
  }
}

export type TSearchResult = any

/**
 * Options for creating a search function.
 */
export interface CreateSearchFunctionOptions {
  functionName?: string
  description?: string
  outputType?: 'str' | 'TextSearchResult' | 'Any'
  parameters?: KernelParameterMetadata[] | null
  returnParameter?: KernelParameterMetadata | null
  filter?: string | ((options: SearchOptions) => void) | Array<string | ((options: SearchOptions) => void)> | null
  top?: number
  skip?: number
  includeTotalCount?: boolean
  filterUpdateFunction?: DynamicFilterFunction | null
  stringMapper?: ((result: TSearchResult) => string) | null
}

/**
 * The base class for all text searchers.
 * @releaseCandidate
 */
export abstract class TextSearch {
  /**
   * The options class for the search.
   */
  get optionsClass(): typeof SearchOptions {
    return SearchOptions
  }

  /**
   * Create a kernel function from a search function.
   */
  createSearchFunction(options: CreateSearchFunctionOptions = {}): KernelFunction {
    const {
      functionName = DEFAULT_FUNCTION_NAME,
      description = DEFAULT_DESCRIPTION,
      outputType = 'str',
      parameters = null,
      returnParameter = null,
      filter = null,
      top = 5,
      skip = 0,
      includeTotalCount = false,
      filterUpdateFunction = null,
      stringMapper = null,
    } = options

    const searchOptions = new SearchOptions({
      filter,
      skip,
      top,
      includeTotalCount,
    })

    switch (outputType) {
      case 'str':
        return this._createKernelFunction({
          outputType: 'string',
          options: searchOptions,
          parameters,
          filterUpdateFunction,
          returnParameter,
          functionName,
          description,
          stringMapper,
        })
      case 'TextSearchResult':
        return this._createKernelFunction({
          outputType: TextSearchResult,
          options: searchOptions,
          parameters,
          filterUpdateFunction,
          returnParameter,
          functionName,
          description,
          stringMapper,
        })
      case 'Any':
        return this._createKernelFunction({
          outputType: 'Any',
          options: searchOptions,
          parameters,
          filterUpdateFunction,
          returnParameter,
          functionName,
          description,
          stringMapper,
        })
      default:
        throw new TextSearchException(
          `Unknown output type: ${outputType}. Must be 'str', 'TextSearchResult', or 'Any'.`
        )
    }
  }

  /**
   * Create a kernel function from a search function.
   */
  private _createKernelFunction(params: {
    outputType: 'string' | typeof TextSearchResult | 'Any'
    options?: SearchOptions | null
    parameters?: KernelParameterMetadata[] | null
    filterUpdateFunction?: DynamicFilterFunction | null
    returnParameter?: KernelParameterMetadata | null
    functionName?: string
    description?: string
    stringMapper?: ((result: TSearchResult) => string) | null
  }): KernelFunction {
    const {
      outputType = 'string',
      options = null,
      parameters = null,
      filterUpdateFunction = null,
      returnParameter = null,
      functionName = DEFAULT_FUNCTION_NAME,
      description = DEFAULT_DESCRIPTION,
      stringMapper = null,
    } = params

    const updateFunc = filterUpdateFunction || defaultDynamicFilterFunction

    const searchWrapper = async (kwargs: Record<string, any>): Promise<string[]> => {
      const query = kwargs.query || ''
      delete kwargs.query

      let innerOptions: SearchOptions
      try {
        // Create a SearchOptions instance if options is a plain object
        const baseOptions = options instanceof SearchOptions ? options : options ? new SearchOptions(options) : null
        innerOptions = createOptions(SearchOptions, baseOptions, kwargs)
      } catch {
        // This usually only happens when the kwargs are invalid, so blank options in this case
        innerOptions = new SearchOptions()
      }

      innerOptions.filter = updateFunc({
        filter: innerOptions.filter,
        parameters,
        ...kwargs,
      })

      try {
        const results = await this.search({
          query,
          outputType: outputType as any,
          ...innerOptions.toObject(),
        })

        return await this._mapResults(results, stringMapper)
      } catch (e) {
        const msg = `Exception in search function: ${e}`
        logger.error(msg)
        throw new TextSearchException(msg)
      }
    }

    return new KernelFunctionFromMethod({
      method: searchWrapper,
      name: functionName,
      description,
      parameters: parameters === null ? DEFAULT_PARAMETER_METADATA : parameters,
      returnParameter: returnParameter || DEFAULT_RETURN_PARAMETER_METADATA,
    })
  }

  /**
   * Map search results to strings.
   */
  private async _mapResults(
    results: KernelSearchResults<TSearchResult>,
    stringMapper?: ((result: TSearchResult) => string) | null
  ): Promise<string[]> {
    const mapped: string[] = []

    for await (const result of results.results) {
      if (stringMapper) {
        mapped.push(stringMapper(result))
      } else {
        mapped.push(this._defaultMapToString(result))
      }
    }

    return mapped
  }

  /**
   * Default mapping function for text search results.
   */
  private _defaultMapToString(result: any): string {
    if (result && typeof result.toJSON === 'function') {
      return JSON.stringify(result.toJSON())
    }
    if (typeof result === 'string') {
      return result
    }
    return JSON.stringify(result)
  }

  /**
   * Search for text, returning a KernelSearchResult with a list of strings.
   * @param params - The search parameters
   * @param params.query - The query to search for
   * @param params.outputType - The type of the output, default is 'string'
   * @param params.kwargs - Additional keyword arguments to pass to the search function
   */
  abstract search(params: {
    query: string
    outputType?: 'string' | typeof TextSearchResult | 'Any'
    [key: string]: any
  }): Promise<KernelSearchResults<TSearchResult>>
}
