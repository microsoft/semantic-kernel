import { BlockTypes } from './block-types'

/**
 * Configuration for a block.
 */
export interface BlockConfig {
  /**
   * The content of the block.
   */
  content: string
}

/**
 * A block.
 */
export class Block {
  /**
   * The type of the block.
   */
  public static readonly type: BlockTypes = BlockTypes.UNDEFINED

  /**
   * The content of the block.
   */
  public content: string

  /**
   * Creates a new Block instance.
   * @param config - The configuration for the block.
   */
  constructor(config: BlockConfig) {
    this.content = config.content.trim()
  }
}
