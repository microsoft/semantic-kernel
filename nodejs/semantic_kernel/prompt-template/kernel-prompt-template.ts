import { TemplateRenderException } from '../exceptions/template-engine-exceptions'
import { KernelArguments } from '../functions/kernel-arguments'
import { Kernel } from '../kernel'
import { Block } from '../template-engine/blocks/block'
import { BlockTypes } from '../template-engine/blocks/block-types'
import { NamedArgBlock } from '../template-engine/blocks/named-arg-block'
import { VarBlock } from '../template-engine/blocks/var-block'
import { TemplateTokenizer } from '../template-engine/template-tokenizer'
import { KERNEL_TEMPLATE_FORMAT_NAME } from './const'
import { InputVariable } from './input-variable'
import { PromptTemplateBase } from './prompt-template-base'
import { PromptTemplateConfig } from './prompt-template-config'

/**
 * HTML escape function for string encoding.
 * @param str - The string to escape.
 * @returns The escaped string.
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
 * Create a Kernel prompt template.
 *
 * This class provides a template engine that supports the Semantic Kernel template format.
 * It extracts blocks (text, variables, function calls) from the template and renders them
 * using the provided kernel and arguments.
 */
export class KernelPromptTemplate extends PromptTemplateBase {
  private _blocks: Block[] = []

  /**
   * Creates a new KernelPromptTemplate instance.
   * @param promptTemplateConfig - The prompt template configuration.
   * @param allowDangerouslySetContent - Whether to allow dangerous content without encoding.
   * @throws Error if the template format is not 'semantic-kernel'.
   */
  constructor(promptTemplateConfig: PromptTemplateConfig, allowDangerouslySetContent: boolean = false) {
    super(promptTemplateConfig, allowDangerouslySetContent)

    // Validate the template format
    if (promptTemplateConfig.templateFormat !== KERNEL_TEMPLATE_FORMAT_NAME) {
      throw new Error(
        `Invalid prompt template format: ${promptTemplateConfig.templateFormat}. Expected: ${KERNEL_TEMPLATE_FORMAT_NAME}`
      )
    }

    // Initialize blocks and extract variables
    this._blocks = this.extractBlocks()
    this._discoverInputVariables()
  }

  /**
   * Given the prompt template, extract all the blocks (text, variables, function calls).
   * @returns An array of blocks extracted from the template.
   */
  private extractBlocks(): Block[] {
    console.debug(`Extracting blocks from template: ${this.promptTemplateConfig.template}`)
    if (!this.promptTemplateConfig.template) {
      return []
    }
    return TemplateTokenizer.tokenize(this.promptTemplateConfig.template)
  }

  /**
   * Discover input variables from the blocks and add them to the template config.
   * This examines all blocks to find variable references and ensures they are
   * registered as input variables.
   */
  private _discoverInputVariables(): void {
    // Add all of the existing input variables to our known set. We'll avoid adding any
    // dynamically discovered input variables with the same name.
    const seen = new Set<string>(this.promptTemplateConfig.inputVariables.map((iv) => iv.name.toLowerCase()))

    // Enumerate every block in the template, adding any variables that are referenced.
    for (const block of this._blocks) {
      const blockType = (block.constructor as typeof Block).type

      if (blockType === BlockTypes.VARIABLE) {
        // Add all variables from variable blocks, e.g. "{{$a}}".
        const varBlock = block as VarBlock
        this._addIfMissing(varBlock.name, seen)
        continue
      }

      if (blockType === BlockTypes.CODE) {
        // For code blocks, we need to inspect the tokens
        // Note: CodeBlock implementation is needed to properly handle this
        // For now, we'll use a type assertion knowing it should have tokens
        const codeBlock = block as any
        if (codeBlock.tokens && Array.isArray(codeBlock.tokens)) {
          for (const token of codeBlock.tokens) {
            const tokenType = (token.constructor as typeof Block).type

            if (tokenType === BlockTypes.VARIABLE) {
              // Add all variables from code blocks, e.g. "{{p.bar $b}}".
              const varBlock = token as VarBlock
              this._addIfMissing(varBlock.name, seen)
              continue
            }

            if (tokenType === BlockTypes.NAMED_ARG) {
              const namedArgBlock = token as NamedArgBlock
              if (namedArgBlock.variable) {
                // Add all variables from named arguments, e.g. "{{p.bar b=$b}}".
                // This represents a named argument for a function call.
                // For example, in the template {{ MyPlugin.MyFunction var1=$boo }}, var1=$boo
                // is a named arg block.
                this._addIfMissing(namedArgBlock.variable.name, seen)
              }
            }
          }
        }
      }
    }
  }

  /**
   * Add a variable name to the input variables if it's not already present.
   * @param variableName - The name of the variable to add.
   * @param seen - A set of variable names already seen (case-insensitive).
   */
  private _addIfMissing(variableName: string, seen: Set<string>): void {
    // Convert variable_name to lower case to handle case-insensitivity
    if (variableName && !seen.has(variableName.toLowerCase())) {
      seen.add(variableName.toLowerCase())
      this.promptTemplateConfig.inputVariables.push(new InputVariable({ name: variableName }))
    }
  }

  /**
   * Render the prompt template.
   *
   * Using the prompt template, replace the variables with their values
   * and execute the functions replacing their reference with the
   * function result.
   *
   * @param kernel - The kernel to use for functions.
   * @param args - The arguments to use for rendering.
   * @returns The prompt template ready to be used for an AI request.
   */
  public async render(kernel: Kernel, args?: KernelArguments): Promise<string> {
    return await this.renderBlocks(this._blocks, kernel, args)
  }

  /**
   * Given a list of blocks render each block and compose the final result.
   *
   * @param blocks - Template blocks generated by extractBlocks.
   * @param kernel - The kernel to use for functions.
   * @param args - The arguments to use for rendering.
   * @returns The prompt template ready to be used for an AI request.
   * @throws TemplateRenderException if an error occurs during rendering.
   */
  private async renderBlocks(blocks: Block[], kernel: Kernel, args?: KernelArguments): Promise<string> {
    console.debug(`Rendering list of ${blocks.length} blocks`)
    const renderedBlocks: string[] = []
    const arguments_ = this._getTrustedArguments(args || new KernelArguments())
    const allowUnsafeFunctionOutput = this._getAllowDangerouslySetFunctionOutput()

    for (const block of blocks) {
      const blockType = (block.constructor as typeof Block).type

      // TextBlock or blocks that implement TextRenderer interface
      if (blockType === BlockTypes.TEXT || blockType === BlockTypes.VALUE || blockType === BlockTypes.VARIABLE) {
        // These blocks have a render method that takes kernel and arguments
        const renderable = block as any
        if (typeof renderable.render === 'function') {
          renderedBlocks.push(renderable.render(kernel, arguments_))
        }
        continue
      }

      // CodeBlock - blocks that implement CodeRenderer interface
      if (blockType === BlockTypes.CODE) {
        try {
          const codeRenderable = block as any
          if (typeof codeRenderable.renderCode === 'function') {
            const rendered = await codeRenderable.renderCode(kernel, arguments_)
            renderedBlocks.push(allowUnsafeFunctionOutput ? rendered : escapeHtml(rendered))
          } else {
            console.warn(`Code block does not have renderCode method`)
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error)
          console.error(`Error rendering code block: ${message}`)
          throw new TemplateRenderException(`Error rendering code block: ${message}`)
        }
      }
    }

    const prompt = renderedBlocks.join('')
    console.debug(`Rendered prompt: ${prompt}`)
    return prompt
  }

  /**
   * Quick render a Kernel prompt template, only supports text and variable blocks.
   *
   * This is a static utility method for simple template rendering without needing
   * to create a full KernelPromptTemplate instance. It does not support code blocks
   * or function calls.
   *
   * @param template - The template to render.
   * @param args - The arguments to use for rendering.
   * @returns The prompt template ready to be used for an AI request.
   * @throws Error if the template contains code blocks.
   */
  public static quickRender(template: string, args: Record<string, any>): string {
    const blocks = TemplateTokenizer.tokenize(template)

    // Check for code blocks - they are not supported in quick render
    if (blocks.some((block) => (block.constructor as typeof Block).type === BlockTypes.CODE)) {
      throw new Error('Quick render does not support code blocks.')
    }

    // Create a minimal kernel (can be used for non-function rendering)
    const kernel = new Kernel()

    // Convert args to KernelArguments
    const kernelArgs = new KernelArguments()
    for (const [key, value] of Object.entries(args)) {
      kernelArgs.set(key, value)
    }

    return blocks
      .map((block) => {
        const renderable = block as any
        if (typeof renderable.render === 'function') {
          return renderable.render(kernel, kernelArgs)
        }
        return ''
      })
      .join('')
  }
}
