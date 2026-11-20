import { CodeBlockSyntaxError } from '../exceptions/template-engine-exceptions'
import { Block } from './blocks/block'
import { BlockTypes } from './blocks/block-types'
import { FunctionIdBlock } from './blocks/function-id-block'
import { NamedArgBlock } from './blocks/named-arg-block'
import { Symbols } from './blocks/symbols'
import { ValBlock } from './blocks/val-block'
import { VarBlock } from './blocks/var-block'

/**
 * Tokenize the code text into blocks.
 *
 * BNF parsed by CodeTokenizer:
 * [template]       ::= "" | [variable] " " [template]
 *                         | [value] " " [template]
 *                         | [function-call] " " [template]
 * [variable]       ::= "$" [valid-name]
 * [value]          ::= "'" [text] "'" | '"' [text] '"'
 * [function-call]  ::= [function-id] | [function-id] [parameter]
 * [parameter]      ::= [variable] | [value]
 */
export class CodeTokenizer {
  /**
   * Tokenize the code text into blocks.
   * @param text - The code text to tokenize.
   * @returns An array of blocks.
   * @throws CodeBlockSyntaxError if the syntax is invalid.
   */
  public static tokenize(text: string): Block[] {
    // Remove spaces, which are ignored anyway
    text = text ? text.trim() : ''

    // Render None/empty to []
    if (!text) {
      return []
    }

    // 1 char only edge case, var and val blocks are invalid with one char, so it must be a function id block
    if (text.length === 1) {
      return [new FunctionIdBlock({ content: text })]
    }

    // Track what type of token we're reading
    let currentTokenType: BlockTypes | null = null

    // Track the content of the current token
    const currentTokenContent: string[] = []

    // Other state we need to track
    let textValueDelimiter: string | null = null
    let spaceSeparatorFound = false
    let skipNextChar = false
    let nextChar = ''
    const blocks: Block[] = []

    for (let index = 0; index < text.length - 1; index++) {
      const currentChar = text[index]
      nextChar = text[index + 1]

      if (skipNextChar) {
        skipNextChar = false
        continue
      }

      // First char is easy
      if (index === 0) {
        if (currentChar === Symbols.VAR_PREFIX) {
          currentTokenType = BlockTypes.VARIABLE
        } else if (currentChar === Symbols.DBL_QUOTE || currentChar === Symbols.SGL_QUOTE) {
          currentTokenType = BlockTypes.VALUE
          textValueDelimiter = currentChar
        } else {
          currentTokenType = BlockTypes.FUNCTION_ID
        }

        currentTokenContent.push(currentChar)
        continue
      }

      // While reading values between quotes
      if (currentTokenType === BlockTypes.VALUE) {
        // If the current char is escaping the next special char we:
        //  - skip the current char (escape char)
        //  - add the next char (special char)
        //  - jump to the one after (to handle "\\" properly)
        if (
          currentChar === Symbols.ESCAPE_CHAR &&
          (nextChar === Symbols.DBL_QUOTE || nextChar === Symbols.SGL_QUOTE || nextChar === Symbols.ESCAPE_CHAR)
        ) {
          currentTokenContent.push(nextChar)
          skipNextChar = true
          continue
        }

        currentTokenContent.push(currentChar)

        // When we reach the end of the value, we add the block
        if (currentChar === textValueDelimiter) {
          blocks.push(new ValBlock({ content: currentTokenContent.join('') }))
          currentTokenContent.length = 0
          currentTokenType = null
          spaceSeparatorFound = false
        }

        continue
      }

      // If we're not between quotes, a space signals the end of the current token
      // Note: there might be multiple consecutive spaces
      if (
        currentChar === Symbols.SPACE ||
        currentChar === Symbols.NEW_LINE ||
        currentChar === Symbols.CARRIAGE_RETURN ||
        currentChar === Symbols.TAB
      ) {
        if (currentTokenType === BlockTypes.VARIABLE) {
          blocks.push(new VarBlock({ content: currentTokenContent.join('') }))
          currentTokenContent.length = 0
        } else if (currentTokenType === BlockTypes.FUNCTION_ID) {
          if (currentTokenContent.includes(Symbols.NAMED_ARG_BLOCK_SEPARATOR)) {
            blocks.push(new NamedArgBlock({ content: currentTokenContent.join('') }))
          } else {
            blocks.push(new FunctionIdBlock({ content: currentTokenContent.join('') }))
          }
          currentTokenContent.length = 0
        }

        spaceSeparatorFound = true
        currentTokenType = null

        continue
      }

      // If we're not inside a quoted value, and we're not processing a space
      currentTokenContent.push(currentChar)

      if (currentTokenType === null) {
        if (!spaceSeparatorFound) {
          throw new CodeBlockSyntaxError('Tokens must be separated by one space least')
        }

        if (currentChar === Symbols.DBL_QUOTE || currentChar === Symbols.SGL_QUOTE) {
          // A quoted value starts here
          currentTokenType = BlockTypes.VALUE
          textValueDelimiter = currentChar
        } else if (currentChar === Symbols.VAR_PREFIX) {
          // A variable starts here
          currentTokenType = BlockTypes.VARIABLE
        } else {
          // A function id starts here
          currentTokenType = BlockTypes.FUNCTION_ID
        }
      }
    }

    // end of main for loop

    // Capture last token
    currentTokenContent.push(nextChar)

    if (currentTokenType === BlockTypes.VALUE) {
      blocks.push(new ValBlock({ content: currentTokenContent.join('') }))
    } else if (currentTokenType === BlockTypes.VARIABLE) {
      blocks.push(new VarBlock({ content: currentTokenContent.join('') }))
    } else if (currentTokenType === BlockTypes.FUNCTION_ID) {
      if (currentTokenContent.includes(Symbols.NAMED_ARG_BLOCK_SEPARATOR)) {
        blocks.push(new NamedArgBlock({ content: currentTokenContent.join('') }))
      } else {
        blocks.push(new FunctionIdBlock({ content: currentTokenContent.join('') }))
      }
    } else {
      throw new CodeBlockSyntaxError('Tokens must be separated by one space least')
    }

    return blocks
  }
}
