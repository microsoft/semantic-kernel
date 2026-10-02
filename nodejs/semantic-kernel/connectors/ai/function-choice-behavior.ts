// Copyright (c) Microsoft. All rights reserved.

import { FunctionCallChoiceConfiguration } from './function-call-choice-configuration'
import { combineFilterDicts } from './function-calling-utils'
import { FunctionChoiceType } from './function-choice-type'

const DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5

/**
 * Filter types for function choice behavior.
 */
export type FunctionFilters = {
  excludedPlugins?: string[]
  includedPlugins?: string[]
  excludedFunctions?: string[]
  includedFunctions?: string[]
}

/**
 * Prompt execution settings interface (minimal).
 */
export interface PromptExecutionSettings {
  [key: string]: any
}

/**
 * Kernel interface (minimal).
 */
export interface Kernel {
  getListOfFunctionMetadata(filters: FunctionFilters): any[]
  getFullListOfFunctionMetadata(): any[]
}

/**
 * Update settings callback type.
 */
export type UpdateSettingsCallback = (
  config: FunctionCallChoiceConfiguration,
  settings: PromptExecutionSettings,
  type?: FunctionChoiceType
) => void

/**
 * Class that controls function choice behavior.
 *
 * @experimental This class is experimental and may change in the future.
 */
export class FunctionChoiceBehavior {
  enableKernelFunctions: boolean = true
  maximumAutoInvokeAttempts: number = DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS
  filters?: FunctionFilters
  type?: FunctionChoiceType

  constructor(options?: {
    enableKernelFunctions?: boolean
    maximumAutoInvokeAttempts?: number
    filters?: FunctionFilters
    type?: FunctionChoiceType
  }) {
    if (options) {
      this.enableKernelFunctions = options.enableKernelFunctions ?? true
      this.maximumAutoInvokeAttempts = options.maximumAutoInvokeAttempts ?? DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS
      this.filters = options.filters
      this.type = options.type
    }
  }

  /**
   * Check if the kernel functions should be auto-invoked.
   * Determined as maximumAutoInvokeAttempts > 0.
   */
  get autoInvokeKernelFunctions(): boolean {
    return this.maximumAutoInvokeAttempts > 0
  }

  /**
   * Set the auto_invoke_kernel_functions property.
   */
  set autoInvokeKernelFunctions(value: boolean) {
    this.maximumAutoInvokeAttempts = value ? DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS : 0
  }

  /**
   * Check for missing functions and get the function call choice configuration.
   *
   * @private
   */
  private checkAndGetConfig(kernel: Kernel, filters?: FunctionFilters): FunctionCallChoiceConfiguration {
    if (filters) {
      return new FunctionCallChoiceConfiguration({
        availableFunctions: kernel.getListOfFunctionMetadata(filters),
      })
    }
    return new FunctionCallChoiceConfiguration({
      availableFunctions: kernel.getFullListOfFunctionMetadata(),
    })
  }

  /**
   * Configure the function choice behavior.
   *
   * @param kernel - The kernel instance
   * @param updateSettingsCallback - Callback to update settings
   * @param settings - The prompt execution settings
   */
  configure(kernel: Kernel, updateSettingsCallback: UpdateSettingsCallback, settings: PromptExecutionSettings): void {
    if (!this.enableKernelFunctions) {
      return
    }

    const config = this.getConfig(kernel)

    if (config) {
      updateSettingsCallback(config, settings, this.type)
    }
  }

  /**
   * Get the function call choice configuration based on the type.
   *
   * @param kernel - The kernel instance
   * @returns The function call choice configuration
   */
  getConfig(kernel: Kernel): FunctionCallChoiceConfiguration {
    return this.checkAndGetConfig(kernel, this.filters)
  }

  /**
   * Creates a FunctionChoiceBehavior with type AUTO.
   *
   * Returns FunctionChoiceBehavior with auto_invoke enabled, and the desired functions
   * based on either the specified filters or the full qualified names. The model will decide which function
   * to use, if any.
   *
   * @param autoInvoke - Whether to enable auto invoke (default: true)
   * @param filters - Filters for function selection
   * @param options - Additional options
   * @returns A new FunctionChoiceBehavior instance
   */
  static Auto(
    autoInvoke: boolean = true,
    filters?: FunctionFilters,
    options?: Partial<FunctionChoiceBehavior>
  ): FunctionChoiceBehavior {
    const maximumAutoInvokeAttempts =
      options?.maximumAutoInvokeAttempts ?? (autoInvoke ? DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS : 0)

    return new FunctionChoiceBehavior({
      type: FunctionChoiceType.AUTO,
      filters,
      maximumAutoInvokeAttempts,
      ...options,
    })
  }

  /**
   * Creates a FunctionChoiceBehavior with type NONE.
   *
   * Returns FunctionChoiceBehavior with auto_invoke disabled, and the desired functions
   * based on either the specified filters or the full qualified names. The model does not invoke any functions,
   * but can rather describe how it would invoke a function to complete a given task/query.
   *
   * @param filters - Filters for function selection
   * @param options - Additional options
   * @returns A new FunctionChoiceBehavior instance
   */
  static NoneInvoke(filters?: FunctionFilters, options?: Partial<FunctionChoiceBehavior>): FunctionChoiceBehavior {
    const maximumAutoInvokeAttempts = options?.maximumAutoInvokeAttempts ?? 0

    return new FunctionChoiceBehavior({
      type: FunctionChoiceType.NONE,
      filters,
      maximumAutoInvokeAttempts,
      ...options,
    })
  }

  /**
   * Creates a FunctionChoiceBehavior with type REQUIRED.
   *
   * Returns FunctionChoiceBehavior with auto_invoke enabled, and the desired functions
   * based on either the specified filters or the full qualified names. The model is required to use one of the
   * provided functions to complete a given task/query.
   *
   * @param autoInvoke - Whether to enable auto invoke (default: true)
   * @param filters - Filters for function selection
   * @param options - Additional options
   * @returns A new FunctionChoiceBehavior instance
   */
  static Required(
    autoInvoke: boolean = true,
    filters?: FunctionFilters,
    options?: Partial<FunctionChoiceBehavior>
  ): FunctionChoiceBehavior {
    const maximumAutoInvokeAttempts = options?.maximumAutoInvokeAttempts ?? (autoInvoke ? 1 : 0)

    return new FunctionChoiceBehavior({
      type: FunctionChoiceType.REQUIRED,
      filters,
      maximumAutoInvokeAttempts,
      ...options,
    })
  }

  /**
   * Create a FunctionChoiceBehavior from a dictionary.
   *
   * @param data - The data object
   * @returns A new FunctionChoiceBehavior instance
   */
  static fromDict(data: Record<string, any>): FunctionChoiceBehavior {
    const dataCopy = { ...data }
    const behaviorType = dataCopy.type || 'auto'
    const autoInvoke = dataCopy.autoInvoke || false
    const functions = dataCopy.functions
    let filters = dataCopy.filters

    delete dataCopy.type
    delete dataCopy.autoInvoke
    delete dataCopy.functions
    delete dataCopy.filters

    if (functions && Array.isArray(functions)) {
      const validFqns = functions.map((name: string) => name.replace('.', '-'))
      if (filters) {
        // Convert FunctionFilters to Record<string, string[]> for combineFilterDicts
        const filtersDict: Record<string, string[]> = {}
        if (filters.excludedPlugins) filtersDict.excludedPlugins = filters.excludedPlugins
        if (filters.includedPlugins) filtersDict.includedPlugins = filters.includedPlugins
        if (filters.excludedFunctions) filtersDict.excludedFunctions = filters.excludedFunctions
        if (filters.includedFunctions) filtersDict.includedFunctions = filters.includedFunctions

        const combined = combineFilterDicts(filtersDict, { includedFunctions: validFqns })
        filters = combined as FunctionFilters
      } else {
        filters = { includedFunctions: validFqns }
      }
    }

    const typeMap: Record<
      string,
      (autoInvoke: boolean, filters?: FunctionFilters, options?: any) => FunctionChoiceBehavior
    > = {
      auto: (ai, f, o) => FunctionChoiceBehavior.Auto(ai, f, o),
      none: (_ai, f, o) => FunctionChoiceBehavior.NoneInvoke(f, o),
      required: (ai, f, o) => FunctionChoiceBehavior.Required(ai, f, o),
    }

    const creator = typeMap[behaviorType.toLowerCase()]
    if (!creator) {
      throw new Error(`Unknown function choice behavior type: ${behaviorType}`)
    }

    return creator(autoInvoke, filters, dataCopy)
  }

  /**
   * Create a FunctionChoiceBehavior from a string.
   *
   * This method converts the provided string to a FunctionChoiceBehavior object
   * for the specified type.
   *
   * @param data - The type string ('auto', 'none', or 'required')
   * @returns A new FunctionChoiceBehavior instance
   */
  static fromString(data: string): FunctionChoiceBehavior {
    const typeValue = data.toLowerCase()

    if (typeValue === 'auto') {
      return FunctionChoiceBehavior.Auto()
    }
    if (typeValue === 'none') {
      return FunctionChoiceBehavior.NoneInvoke()
    }
    if (typeValue === 'required') {
      return FunctionChoiceBehavior.Required()
    }

    throw new Error(
      `The specified type \`${typeValue}\` is not supported. Allowed types are: \`auto\`, \`none\`, \`required\`.`
    )
  }
}
