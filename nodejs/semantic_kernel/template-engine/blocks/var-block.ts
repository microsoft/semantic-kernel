import { VarBlockRenderError, VarBlockSyntaxError } from '../../exceptions/template-engine-exceptions'
import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel } from '../../kernel'
import { Block, BlockConfig } from './block'
import { BlockTypes } from './block-types'
import { Symbols } from './symbols'

const VAR_BLOCK_REGEX = /^[$]{1}(?<name>[0-9A-Za-z_]+)$/

/**
 * Configuration for a variable block.
 */
export interface VarBlockConfig extends BlockConfig {
  /**
   * The name of the variable.
   */
  name?: string
}

/**
 * Create a variable block.
 *
 * A variable block is used to add a variable to a template.
 * It gets rendered from KernelArguments, if the variable is not found
 * a warning is logged and an empty string is returned.
 * The variable must start with $ and be followed by a valid variable name.
 * A valid variable name is a string of letters, numbers and underscores.
 *
 * Examples:
 *   $var
 *   $test_var
 */
export class VarBlock extends Block {
  /**
   * The type of the block.
   */
  public static override readonly type: BlockTypes = BlockTypes.VARIABLE

  /**
   * The name of the variable.
   */
  public name: string

  /**
   * Creates a new VarBlock instance.
   * @param config - The configuration for the block.
   * @throws VarBlockSyntaxError if the content does not match the variable syntax.
   */
  constructor(config: VarBlockConfig) {
    super(config)

    // If name is already provided, use it directly
    if (config.name !== undefined) {
      this.name = config.name
    } else {
      // Parse the content to extract the name
      const parsed = this.parseContent(this.content)
      this.name = parsed.name
    }
  }

  /**
   * Parse the content and extract the name.
   * @param content - The content to parse.
   * @returns An object containing the variable name.
   * @throws VarBlockSyntaxError if the content does not match the expected format.
   */
  private parseContent(content: string): { name: string } {
    const matches = VAR_BLOCK_REGEX.exec(content)
    if (!matches || !matches.groups) {
      throw new VarBlockSyntaxError(content)
    }

    const name = matches.groups['name']
    if (!name) {
      throw new VarBlockSyntaxError(content)
    }

    return { name }
  }

  /**
   * Render the variable block with the given arguments.
   *
   * If the variable is not found in the arguments, return an empty string.
   *
   * @param _kernel - The kernel instance (unused).
   * @param args - The kernel arguments.
   * @returns The string value of the variable, or an empty string if not found.
   * @throws VarBlockRenderError if the value cannot be converted to a string.
   */
  public render(_kernel?: Kernel, args?: KernelArguments | null): string {
    if (!args) {
      return ''
    }

    const value = args.get(this.name)
    if (value === undefined || value === null) {
      console.warn(`Variable \`${Symbols.VAR_PREFIX}: ${this.name}\` not found in the KernelArguments`)
      return ''
    }

    try {
      return String(value)
    } catch (e) {
      console.log(`Failed to convert variable \`${Symbols.VAR_PREFIX}: ${this.name}\` value to string:`, e)
      throw new VarBlockRenderError(`Block ${this.name} failed to be parsed to a string, type is ${typeof value}`)
    }
  }

  /**
   * Get the raw value of the variable from arguments without converting to string.
   *
   * This is used when passing arguments to functions to preserve their original types.
   *
   * @param args - The kernel arguments to get the value from.
   * @returns The raw value from the arguments, or undefined if not found.
   */
  public getValue(args?: KernelArguments | null): any {
    if (!args) {
      return undefined
    }
    return args.get(this.name)
  }
}
