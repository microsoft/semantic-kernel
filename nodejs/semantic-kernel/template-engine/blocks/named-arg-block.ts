import { NamedArgBlockSyntaxError } from '../../exceptions/template-engine-exceptions'
import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel } from '../../kernel'
import { Block, BlockConfig } from './block'
import { BlockTypes } from './block-types'
import { ValBlock } from './val-block'
import { VarBlock } from './var-block'

const NAMED_ARG_REGEX =
  /^(?<name>[0-9A-Za-z_]+)[=]{1}(?<value>[$]{1}(?<var_name>[0-9A-Za-z_]+)|(?<quote>["'])(?<val>.[^"^']*)(?=\k<quote>)["'])$/

/**
 * Configuration for a named argument block.
 */
export interface NamedArgBlockConfig extends BlockConfig {
  /**
   * The name of the argument.
   */
  name?: string | null

  /**
   * The value of the argument.
   */
  value?: ValBlock | null

  /**
   * The variable of the argument.
   */
  variable?: VarBlock | null
}

/**
 * Create a named argument block.
 *
 * A named arg block is used to add arguments to a function call.
 * It needs to be combined with a function_id block to be useful.
 * Inside a code block, if the first block is a function_id block,
 * the first block can be a variable or value block, anything else
 * must be a named arg block.
 *
 * The value inside the NamedArgBlock can be a ValBlock or a VarBlock.
 *
 * Examples:
 *   {{ plugin.function arg1=$var }}
 *   {{ plugin.function arg1='value' }}
 *   {{ plugin.function 'value' arg2=$var }}
 *   {{ plugin.function $var arg2='value' }}
 *   {{ plugin_function arg1=$var1 arg2=$var2 arg3='value' }}
 */
export class NamedArgBlock extends Block {
  /**
   * The type of the block.
   */
  public static override readonly type: BlockTypes = BlockTypes.NAMED_ARG

  /**
   * The name of the argument.
   */
  public name: string | null

  /**
   * The value of the argument.
   */
  public value: ValBlock | null

  /**
   * The variable of the argument.
   */
  public variable: VarBlock | null

  /**
   * Creates a new NamedArgBlock instance.
   * @param config - The configuration for the block.
   * @throws NamedArgBlockSyntaxError if the content does not match the named argument syntax.
   */
  constructor(config: NamedArgBlockConfig) {
    super(config)

    // If name and either value or variable are provided, use them directly
    if (config.name !== undefined && (config.value !== undefined || config.variable !== undefined)) {
      this.name = config.name
      this.value = config.value ?? null
      this.variable = config.variable ?? null
    } else {
      // Parse the content to extract name and value/variable
      const parsed = this.parseContent(this.content)
      this.name = parsed.name
      this.value = parsed.value
      this.variable = parsed.variable
    }
  }

  /**
   * Parse the content of the named argument block and extract the name and value.
   * @param content - The content to parse.
   * @returns An object containing the name and either value or variable.
   * @throws NamedArgBlockSyntaxError if the content does not match the expected format.
   */
  private parseContent(content: string): { name: string | null; value: ValBlock | null; variable: VarBlock | null } {
    const matches = NAMED_ARG_REGEX.exec(content)
    if (!matches || !matches.groups) {
      throw new NamedArgBlockSyntaxError(content)
    }

    const matchesDict = matches.groups
    const name = matchesDict['name'] || null
    let value: ValBlock | null = null
    let variable: VarBlock | null = null

    const valueContent = matchesDict['value']
    if (valueContent) {
      if (matchesDict['var_name']) {
        variable = new VarBlock({ content: valueContent, name: matchesDict['var_name'] })
      } else if (matchesDict['val'] !== undefined) {
        value = new ValBlock({ content: valueContent, value: matchesDict['val'], quote: matchesDict['quote'] })
      }
    }

    return { name, value, variable }
  }

  /**
   * Render the named argument block.
   * @param kernel - The kernel instance.
   * @param args - The kernel arguments.
   * @returns The rendered value.
   */
  public render(kernel?: Kernel, args?: KernelArguments | null): any {
    if (this.value) {
      return this.value.render()
    }
    if (!args) {
      return ''
    }
    if (this.variable) {
      return this.variable.render(kernel, args)
    }
    return null
  }
}
