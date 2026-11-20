import { ValBlockSyntaxError } from '../../exceptions/template-engine-exceptions'
import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel } from '../../kernel'
import { Block, BlockConfig } from './block'
import { BlockTypes } from './block-types'

const VAL_BLOCK_REGEX = /^(?<quote>["'])(?<value>.*)(?=\k<quote>)["']$/s

/**
 * Configuration for a value block.
 */
export interface ValBlockConfig extends BlockConfig {
  /**
   * The value of the block.
   */
  value?: string | null

  /**
   * The quote used to wrap the value.
   */
  quote?: string | null
}

/**
 * Create a value block.
 *
 * A value block is used to represent a value in a template.
 * It can be used to represent any characters.
 * It needs to start and end with the same quote character,
 * can be both single or double quotes, as long as they are not mixed.
 *
 * Examples:
 *   'value'
 *   "value"
 *   'value with "quotes"'
 *   "value with 'quotes'"
 */
export class ValBlock extends Block {
  /**
   * The type of the block.
   */
  public static override readonly type: BlockTypes = BlockTypes.VALUE

  /**
   * The value of the block.
   */
  public value: string | null

  /**
   * The quote used to wrap the value.
   */
  public quote: string | null

  /**
   * Creates a new ValBlock instance.
   * @param config - The configuration for the block.
   * @throws ValBlockSyntaxError if the content does not match the value block syntax.
   */
  constructor(config: ValBlockConfig) {
    super(config)

    // If value is already provided, use it directly
    if (config.value !== undefined) {
      this.value = config.value
      this.quote = config.quote ?? "'"
    } else {
      // Parse the content to extract value and quote
      const parsed = this.parseContent(this.content)
      this.value = parsed.value
      this.quote = parsed.quote
    }
  }

  /**
   * Parse the content and extract the value and quote.
   * @param content - The content to parse.
   * @returns An object containing the value and quote.
   * @throws ValBlockSyntaxError if the content does not match the expected format.
   */
  private parseContent(content: string): { value: string | null; quote: string | null } {
    const matches = VAL_BLOCK_REGEX.exec(content)
    if (!matches || !matches.groups) {
      throw new ValBlockSyntaxError(content)
    }

    const value = matches.groups['value'] || null
    const quote = matches.groups['quote'] || null

    return { value, quote }
  }

  /**
   * Render the value block.
   * @param _kernel - The kernel instance (unused).
   * @param _arguments - The kernel arguments (unused).
   * @returns The value of the block.
   */
  public render(_kernel?: Kernel, _arguments?: KernelArguments | null): string {
    return this.value || ''
  }
}
