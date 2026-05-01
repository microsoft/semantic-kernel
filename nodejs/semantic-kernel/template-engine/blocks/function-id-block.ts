import { FunctionIdBlockSyntaxError } from '../../exceptions/template-engine-exceptions'
import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel } from '../../kernel'
import { Block, BlockConfig } from './block'
import { BlockTypes } from './block-types'

const FUNCTION_ID_BLOCK_REGEX = /^((?<plugin>[0-9A-Za-z_]+)[.])?(?<function>[0-9A-Za-z_]+)$/

/**
 * Configuration for a function ID block.
 */
export interface FunctionIdBlockConfig extends BlockConfig {
  /**
   * The function name.
   */
  functionName?: string

  /**
   * The plugin name.
   */
  pluginName?: string | null
}

/**
 * Block to represent a function id. It can be used to call a function from a plugin.
 *
 * The content is parsed using a regex, that returns either a plugin and
 * function name or just a function name, depending on the content.
 *
 * Anything other than that and a FunctionIdBlockSyntaxError is raised.
 */
export class FunctionIdBlock extends Block {
  /**
   * The type of the block.
   */
  public static override readonly type: BlockTypes = BlockTypes.FUNCTION_ID

  /**
   * The function name.
   */
  public functionName: string

  /**
   * The plugin name.
   */
  public pluginName: string | null

  /**
   * Creates a new FunctionIdBlock instance.
   * @param config - The configuration for the block.
   * @throws FunctionIdBlockSyntaxError if the content does not have valid syntax.
   */
  constructor(config: FunctionIdBlockConfig) {
    super(config)

    // If both functionName and pluginName are provided, use them directly
    if (config.functionName !== undefined && config.pluginName !== undefined) {
      this.functionName = config.functionName
      this.pluginName = config.pluginName
    } else {
      // Parse the content to extract plugin and function names
      const parsed = this.parseContent(this.content)
      this.functionName = parsed.functionName
      this.pluginName = parsed.pluginName
    }
  }

  /**
   * Parse the content of the function id block and extract the plugin and function name.
   * @param content - The content to parse.
   * @returns An object containing the plugin name and function name.
   * @throws FunctionIdBlockSyntaxError if the content does not match the expected format.
   */
  private parseContent(content: string): { pluginName: string | null; functionName: string } {
    const matches = FUNCTION_ID_BLOCK_REGEX.exec(content)
    if (!matches || !matches.groups) {
      throw new FunctionIdBlockSyntaxError(content)
    }

    const pluginName = matches.groups['plugin'] || null
    const functionName = matches.groups['function']

    return { pluginName, functionName }
  }

  /**
   * Render the function id block.
   * @param _kernel - The kernel instance (unused).
   * @param _arguments - The kernel arguments (unused).
   * @returns The content of the block.
   */
  public render(_kernel?: Kernel, _arguments?: KernelArguments | null): string {
    return this.content
  }
}
