import { BlockSyntaxError, CodeBlockTokenError, TemplateSyntaxError } from '../exceptions/template-engine-exceptions'
import { Block } from './blocks/block'
import { BlockTypes } from './blocks/block-types'
import { Symbols } from './blocks/symbols'
import { TextBlock } from './blocks/text-block'
import { CodeTokenizer } from './code-tokenizer'

/**
 * Tokenize the template text into blocks.
 *
 * BNF parsed by TemplateTokenizer:
 * [template]       ::= "" | [block] | [block] [template]
 * [block]          ::= [sk-block] | [text-block]
 * [sk-block]       ::= "{{" [variable] "}}"
 *                      | "{{" [value] "}}"
 *                      | "{{" [function-call] "}}"
 * [text-block]     ::= [any-char] | [any-char] [text-block]
 * [any-char]       ::= any char
 */
export class TemplateTokenizer {
  /**
   * Tokenize the template text into blocks.
   * @param text - The template text to tokenize.
   * @returns An array of blocks.
   * @throws TemplateSyntaxError if the template syntax is invalid.
   */
  public static tokenize(text: string): Block[] {
    // An empty block consists of 4 chars: "{{}}"
    const EMPTY_CODE_BLOCK_LENGTH = 4
    // A block shorter than 5 chars is either empty or
    // invalid, e.g. "{{ }}" and "{{$}}"
    const MIN_CODE_BLOCK_LENGTH = EMPTY_CODE_BLOCK_LENGTH + 1

    text = text || ''

    // Render None/empty to ""
    if (!text) {
      return [TextBlock.fromText('')]
    }

    // If the template is "empty" return it as a text block
    if (text.length < MIN_CODE_BLOCK_LENGTH) {
      return [TextBlock.fromText(text)]
    }

    const blocks: Block[] = []
    let endOfLastBlock = 0
    let blockStartPos = 0
    let blockStartFound = false
    let insideTextValue = false
    let textValueDelimiter: string | null = null
    let skipNextChar = false

    for (let currentCharPos = 0; currentCharPos < text.length - 1; currentCharPos++) {
      const currentChar = text[currentCharPos]
      const nextCharPos = currentCharPos + 1
      const nextChar = text[nextCharPos]

      if (skipNextChar) {
        skipNextChar = false
        continue
      }

      // When "{{" is found outside a value
      // Note: "{{ {{x}}" => ["{{ ", "{{x}}"]
      if (!insideTextValue && currentChar === Symbols.BLOCK_STARTER && nextChar === Symbols.BLOCK_STARTER) {
        // A block starts at the first "{"
        blockStartPos = currentCharPos
        blockStartFound = true
      }

      if (!blockStartFound) {
        continue
      }

      // After having found "{{"
      if (insideTextValue) {
        // While inside a text value, when the end quote is found
        // If the current char is escaping the next special char we skip
        if (
          currentChar === Symbols.ESCAPE_CHAR &&
          (nextChar === Symbols.DBL_QUOTE || nextChar === Symbols.SGL_QUOTE || nextChar === Symbols.ESCAPE_CHAR)
        ) {
          skipNextChar = true
          continue
        }

        if (currentChar === textValueDelimiter) {
          insideTextValue = false
        }
        continue
      }

      // A value starts here
      if (currentChar === Symbols.DBL_QUOTE || currentChar === Symbols.SGL_QUOTE) {
        insideTextValue = true
        textValueDelimiter = currentChar
        continue
      }

      // If the block ends here
      if (currentChar === Symbols.BLOCK_ENDER && nextChar === Symbols.BLOCK_ENDER) {
        blocks.push(...TemplateTokenizer._extractBlocks(text, blockStartPos, endOfLastBlock, nextCharPos))
        endOfLastBlock = nextCharPos + 1
        blockStartFound = false
      }
    }

    // If there is something left after the last block, capture it as a TextBlock
    if (endOfLastBlock < text.length) {
      blocks.push(TextBlock.fromText(text, endOfLastBlock, text.length))
    }

    return blocks
  }

  /**
   * Extract the blocks from the found code.
   *
   * If there is text before the current block, create a TextBlock from that.
   *
   * If the block is empty, return a TextBlock with the delimiters.
   *
   * If the block is not empty, tokenize it and return the result.
   * If there is only a variable or value in the code block,
   * return just that, instead of the CodeBlock.
   *
   * @param text - The full template text.
   * @param blockStartPos - The start position of the block.
   * @param endOfLastBlock - The end position of the last block.
   * @param nextCharPos - The position of the next character after the block end.
   * @returns An array of blocks extracted.
   * @throws TemplateSyntaxError if the code block cannot be tokenized.
   */
  private static _extractBlocks(
    text: string,
    blockStartPos: number,
    endOfLastBlock: number,
    nextCharPos: number
  ): Block[] {
    const newBlocks: Block[] = []

    if (blockStartPos > endOfLastBlock) {
      newBlocks.push(TextBlock.fromText(text, endOfLastBlock, blockStartPos))
    }

    const contentWithDelimiters = text.substring(blockStartPos, nextCharPos + 1)
    const contentWithoutDelimiters = contentWithDelimiters.substring(2, contentWithDelimiters.length - 2).trim()

    if (contentWithoutDelimiters.length === 0) {
      // If what is left is empty (only {{}}), consider the raw block
      // a TextBlock
      newBlocks.push(TextBlock.fromText(contentWithDelimiters))
      return newBlocks
    }

    let codeBlocks: Block[]
    try {
      codeBlocks = CodeTokenizer.tokenize(contentWithoutDelimiters)
    } catch (e) {
      if (e instanceof BlockSyntaxError) {
        const msg = `Failed to tokenize code block: ${contentWithoutDelimiters}. ${e}`
        console.warn(msg)
        throw new TemplateSyntaxError(msg)
      }
      throw e
    }

    // Check if the first block is a value or variable
    const firstBlockType = (codeBlocks[0].constructor as typeof Block).type
    if (firstBlockType === BlockTypes.VALUE || firstBlockType === BlockTypes.VARIABLE) {
      newBlocks.push(codeBlocks[0])
      return newBlocks
    }

    // For CodeBlock, we would need to import and create it
    // For now, we'll add the logic placeholder
    try {
      // This would require CodeBlock implementation
      // newBlocks.push(new CodeBlock({ content: contentWithoutDelimiters, tokens: codeBlocks }))
      // For now, just add the first block as a fallback
      newBlocks.push(codeBlocks[0])
      return newBlocks
    } catch (e) {
      if (e instanceof CodeBlockTokenError) {
        const msg = `Failed to tokenize code block: ${contentWithoutDelimiters}. ${e}`
        console.warn(msg)
        throw new TemplateSyntaxError(msg)
      }
      throw e
    }
  }
}
