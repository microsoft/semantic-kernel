import { KernelArguments } from '../../functions/kernel-arguments'
import { Kernel } from '../../kernel'
import { Block, BlockConfig } from './block'
import { BlockTypes } from './block-types'

/**
 * A block with text content.
 */
export class TextBlock extends Block {
  /**
   * The type of the block.
   */
  public static override readonly type: BlockTypes = BlockTypes.TEXT

  /**
   * Creates a new TextBlock instance.
   * @param config - The configuration for the block.
   */
  constructor(config: BlockConfig) {
    // Text blocks are not stripped, so we override the parent constructor behavior
    super({ content: config.content })
    this.content = config.content
  }

  /**
   * Create a text block from a string.
   * @param text - The text to create the block from.
   * @param startIndex - The start index of the text to extract.
   * @param stopIndex - The stop index of the text to extract.
   * @returns A new TextBlock instance.
   */
  public static fromText(text?: string | null, startIndex?: number, stopIndex?: number): TextBlock {
    if (text === null || text === undefined) {
      return new TextBlock({ content: '' })
    }

    let extractedText = text

    if (startIndex !== undefined && stopIndex !== undefined) {
      if (startIndex > stopIndex) {
        throw new ValueError(`start_index (${startIndex}) must be less than stop_index (${stopIndex})`)
      }

      if (startIndex < 0) {
        throw new ValueError(`start_index (${startIndex}) must be greater than 0`)
      }

      extractedText = text.substring(startIndex, stopIndex)
    } else if (startIndex !== undefined) {
      extractedText = text.substring(startIndex)
    } else if (stopIndex !== undefined) {
      extractedText = text.substring(0, stopIndex)
    }

    return new TextBlock({ content: extractedText })
  }

  /**
   * Render the text block.
   * @param _kernel - The kernel instance (unused).
   * @param _arguments - The kernel arguments (unused).
   * @returns The content of the block.
   */
  public render(_kernel?: Kernel, _arguments?: KernelArguments | null): string {
    return this.content
  }
}

/**
 * Custom ValueError for index validation errors.
 */
class ValueError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ValueError'
  }
}
