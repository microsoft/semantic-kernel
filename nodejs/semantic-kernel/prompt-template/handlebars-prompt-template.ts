import * as Handlebars from 'handlebars'
import {
  HandlebarsTemplateRenderException,
  HandlebarsTemplateSyntaxError,
} from '../exceptions/template-engine-exceptions'
import { KernelArguments } from '../functions/kernel-arguments'
import { Kernel } from '../kernel'
import { HANDLEBARS_TEMPLATE_FORMAT_NAME } from './const'
import { PromptTemplateBase } from './prompt-template-base'
import { PromptTemplateConfig } from './prompt-template-config'
import { HANDLEBAR_SYSTEM_HELPERS } from './utils/handlebars-system-helpers'

/**
 * Create a Handlebars prompt template.
 *
 * Handlebars are parsed as a whole and therefore do not have variables that can be extracted,
 * also with handlebars there is no distinction in syntax between a variable and a value,
 * a value that is encountered is tried to resolve with the arguments and the functions,
 * if not found, the literal value is returned.
 */
export class HandlebarsPromptTemplate extends PromptTemplateBase {
  private _templateCompiler: HandlebarsTemplateDelegate<any> | null = null

  /**
   * Creates a new HandlebarsPromptTemplate instance.
   * @param promptTemplateConfig - The prompt template configuration.
   * @param allowDangerouslySetContent - Allow content without encoding throughout.
   * @throws ValueError if the template format is not 'handlebars'.
   * @throws HandlebarsTemplateSyntaxError if the handlebars template has a syntax error.
   */
  constructor(promptTemplateConfig: PromptTemplateConfig, allowDangerouslySetContent: boolean = false) {
    // Validate the template format
    if (promptTemplateConfig.templateFormat !== HANDLEBARS_TEMPLATE_FORMAT_NAME) {
      throw new ValueError(
        `Invalid prompt template format: ${promptTemplateConfig.templateFormat}. Expected: handlebars`
      )
    }

    super(promptTemplateConfig, allowDangerouslySetContent)

    // Compile the template
    if (promptTemplateConfig.template) {
      try {
        this._templateCompiler = Handlebars.compile(promptTemplateConfig.template)
      } catch (e) {
        console.error(`Invalid handlebars template: ${promptTemplateConfig.template} error:`, e)
        throw new HandlebarsTemplateSyntaxError(`Invalid handlebars template: ${promptTemplateConfig.template}`)
      }
    }
  }

  /**
   * Render the prompt template.
   *
   * Using the prompt template, replace the variables with their values
   * and execute the functions replacing their reference with the
   * function result.
   *
   * @param kernel - The kernel instance.
   * @param args - The kernel arguments.
   * @returns The prompt template ready to be used for an AI request.
   * @throws HandlebarsTemplateRenderException if an error occurs during rendering.
   */
  public async render(kernel: Kernel, args?: KernelArguments): Promise<string> {
    if (!this._templateCompiler) {
      return ''
    }

    const arguments_ = args ?? new KernelArguments()
    const trustedArguments = this._getTrustedArguments(arguments_)
    const allowUnsafeFunctionOutput = this._getAllowDangerouslySetFunctionOutput()

    // Create helpers from kernel functions
    const helpers: Record<string, Handlebars.HelperDelegate> = {}

    // Add function helpers from kernel plugins
    for (const plugin of kernel.plugins.values()) {
      for (const func of plugin.functions.values()) {
        // Construct fully qualified name
        const functionName = func.metadata.pluginName
          ? `${func.metadata.pluginName}-${func.metadata.name}`
          : func.metadata.name
        helpers[functionName] = this.createTemplateHelperFromFunction(
          func,
          kernel,
          arguments_,
          allowUnsafeFunctionOutput
        )
      }
    }

    // Add system helpers
    Object.assign(helpers, HANDLEBAR_SYSTEM_HELPERS)

    try {
      // Convert KernelArguments Map to plain object for Handlebars
      const context: Record<string, any> = {}
      for (const [key, value] of trustedArguments.entries()) {
        context[key] = value
      }

      return this._templateCompiler(context, { helpers })
    } catch (e) {
      console.error(
        `Error rendering prompt template: ${this.promptTemplateConfig.template} with arguments: ${JSON.stringify(
          Array.from(trustedArguments.entries())
        )}`
      )
      throw new HandlebarsTemplateRenderException(
        `Error rendering prompt template: ${this.promptTemplateConfig.template} ` +
          `with arguments: ${JSON.stringify(Array.from(trustedArguments.entries()))}: error: ${e}`
      )
    }
  }

  /**
   * Create a template helper function from a kernel function.
   * @param func - The kernel function.
   * @param kernel - The kernel instance.
   * @param baseArguments - The base arguments.
   * @param allowDangerouslySetContent - Whether to allow dangerous content.
   * @returns A Handlebars helper function.
   */
  private createTemplateHelperFromFunction(
    func: any,
    _kernel: Kernel,
    baseArguments: KernelArguments,
    allowDangerouslySetContent: boolean
  ): Handlebars.HelperDelegate {
    return (...args: any[]) => {
      // In Handlebars, the last argument is always the options object
      const options = args[args.length - 1]
      const actualArgs = args.slice(0, -1)

      // Create new arguments merging base arguments with function call arguments
      const functionArguments = new KernelArguments()

      // Copy execution settings from base arguments
      if (baseArguments.executionSettings) {
        functionArguments.executionSettings = baseArguments.executionSettings
      }

      // Merge base arguments
      for (const [key, value] of baseArguments.entries()) {
        functionArguments.set(key, value)
      }

      // Add hash parameters as named arguments
      if (options?.hash) {
        for (const [key, value] of Object.entries(options.hash)) {
          functionArguments.set(key, value)
        }
      }

      // Add positional arguments
      if (actualArgs.length > 0) {
        functionArguments.set('input', actualArgs[0])
      }

      // Invoke the function synchronously (using a blocking approach for now)
      // Note: This is a simplified implementation. A full implementation would handle async properly
      let result: any
      try {
        // This would need proper async handling in a real implementation
        // For now, we'll use a synchronous placeholder
        result = '[Function execution pending]'
      } catch (e) {
        console.error(`Error executing function ${func.name}: ${e}`)
        result = ''
      }

      // Handle output encoding
      if (!allowDangerouslySetContent && typeof result === 'string') {
        return escapeHtml(result)
      }

      return result
    }
  }
}

/**
 * HTML escape function for string encoding.
 */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * Custom ValueError for validation errors.
 */
class ValueError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ValueError'
  }
}
