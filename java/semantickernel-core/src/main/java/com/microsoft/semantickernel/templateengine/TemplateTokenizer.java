// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine;

import com.microsoft.semantickernel.templateengine.blocks.Block;
import com.microsoft.semantickernel.templateengine.blocks.CodeBlock;
import com.microsoft.semantickernel.templateengine.blocks.Symbols;
import com.microsoft.semantickernel.templateengine.blocks.TextBlock;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/// <summary>
/// Simple tokenizer used for default SK template language.
///
/// BNF parsed by TemplateTokenizer:
/// [template]       ::= "" | [block] | [block] [template]
/// [block]          ::= [sk-block] | [text-block]
/// [sk-block]       ::= "{{" [variable] "}}" | "{{" [value] "}}" | "{{" [function-call] "}}"
/// [text-block]     ::= [any-char] | [any-char] [text-block]
/// [any-char]       ::= any char
///
/// BNF parsed by CodeTokenizer:
/// [template]       ::= "" | [variable] " " [template] | [value] " " [template] | [function-call] "
// " [template]
/// [variable]       ::= "$" [valid-name]
/// [value]          ::= "'" [text] "'" | '"' [text] '"'
/// [function-call]  ::= [function-id] | [function-id] [parameter]
/// [parameter]      ::= [variable] | [value]
///
/// BNF parsed by dedicated blocks
/// [function-id]    ::= [valid-name] | [valid-name] "." [valid-name]
/// [valid-name]     ::= [valid-symbol] | [valid-symbol] [valid-name]
/// [valid-symbol]   ::= [letter] | [digit] | "_"
/// [letter]         ::= "a" | "b" ... | "z" | "A" | "B" ... | "Z"
/// [digit]          ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
/// </summary>
public class TemplateTokenizer {
    /*
        /// <summary>
        /// Create a new instance of SK tokenizer
        /// </summary>
        /// <param name="log"></param>
        public TemplateTokenizer(ILogger? log = null)
        {
            this._log = log ?? NullLogger.Instance;
            this._codeTokenizer = new CodeTokenizer(this._log);
        }
    */
    /// <summary>
    /// Extract blocks from the given text
    /// </summary>
    /// <param name="text">Text to parse</param>
    /// <returns>List of blocks found in the text</returns>
    public List<Block> tokenize(String text) {
        // An empty block consists of 4 chars: "{{}}"
        int EMPTY_CODE_BLOCK_LENGTH = 4;
        // A block shorter than 5 chars is either empty or invalid, e.g. "{{ }}" and "{{$}}"
        int MIN_CODE_BLOCK_LENGTH = EMPTY_CODE_BLOCK_LENGTH + 1;

        // Render NULL to ""
        if (text == null || text.isEmpty()) {
            return Collections.singletonList(new TextBlock(""));
        }

        // If the template is "empty" return the content as a text block
        if (text.length() < MIN_CODE_BLOCK_LENGTH) {
            return Collections.singletonList(new TextBlock(text));
        }

        List<Block> blocks = new ArrayList<>();

        int endOfLastBlock = 0;

        int blockStartPos = 0;
        boolean blockStartFound = false;

        boolean insideTextValue = false;
        char textValueDelimiter = '\0';

        boolean skipNextChar = false;

        char nextChar = text.charAt(0);
        for (int nextCharCursor = 1; nextCharCursor < text.length(); nextCharCursor++) {
            int currentCharPos = nextCharCursor - 1;
            int cursor = nextCharCursor;
            char currentChar = nextChar;
            nextChar = text.charAt(nextCharCursor);

            if (skipNextChar) {
                skipNextChar = false;
                continue;
            }

            // When "{{" is found outside a value
            // Note: "{{ {{x}}" => ["{{ ", "{{x}}"]
            if (!insideTextValue
                    && currentChar == Symbols.BlockStarter
                    && nextChar == Symbols.BlockStarter) {
                // A block starts at the first "{"
                blockStartPos = currentCharPos;
                blockStartFound = true;
            }

            // After having found '{{'
            if (blockStartFound) {
                // While inside a text value, when the end quote is found
                if (insideTextValue) {
                    if (currentChar == Symbols.EscapeChar && canBeEscaped(nextChar)) {
                        skipNextChar = true;
                        continue;
                    }

                    if (currentChar == textValueDelimiter) {
                        insideTextValue = false;
                    }
                } else {
                    // A value starts here
                    if (isQuote(currentChar)) {
                        insideTextValue = true;
                        textValueDelimiter = currentChar;
                    }
                    // If the block ends here
                    else if (currentChar == Symbols.BlockEnder && nextChar == Symbols.BlockEnder) {
                        // If there is plain text between the current var/val/code block and the
                        // previous one, capture that as a TextBlock
                        if (blockStartPos > endOfLastBlock) {
                            blocks.add(new TextBlock(text, endOfLastBlock, blockStartPos));
                        }

                        // Extract raw block
                        String contentWithDelimiters = subStr(text, blockStartPos, cursor + 1);

                        // Remove "{{" and "}}" delimiters and trim empty chars
                        String contentWithoutDelimiters =
                                contentWithDelimiters
                                        .substring(2, contentWithDelimiters.length() - 2)
                                        .trim();

                        if (contentWithoutDelimiters.length() == 0) {
                            // If what is left is empty, consider the raw block a Text Block
                            blocks.add(new TextBlock(contentWithDelimiters));
                        } else {
                            List<Block> codeBlocks =
                                    this.codeTokenizer.tokenize(contentWithoutDelimiters);

                            switch (codeBlocks.get(0).getType()) {
                                case Variable:
                                    if (codeBlocks.size() > 1) {
                                        throw new TemplateException(
                                                TemplateException.ErrorCodes.SYNTAX_ERROR,
                                                "Invalid token detected after the variable: "
                                                        + contentWithoutDelimiters);
                                    }

                                    blocks.add(codeBlocks.get(0));
                                    break;

                                case Value:
                                    if (codeBlocks.size() > 1) {
                                        throw new TemplateException(
                                                TemplateException.ErrorCodes.SYNTAX_ERROR,
                                                "Invalid token detected after the value: "
                                                        + contentWithoutDelimiters);
                                    }

                                    blocks.add(codeBlocks.get(0));
                                    break;

                                case FunctionId:
                                    if (codeBlocks.size() > 2) {
                                        throw new TemplateException(
                                                TemplateException.ErrorCodes.SYNTAX_ERROR,
                                                "Functions support only one parameter: "
                                                        + contentWithoutDelimiters);
                                    }

                                    blocks.add(new CodeBlock(codeBlocks, contentWithoutDelimiters));
                                    break;

                                case Code:
                                case Text:
                                case Undefined:
                                default:
                                    throw new TemplateException(
                                            TemplateException.ErrorCodes.UNEXPECTED_BLOCK_TYPE,
                                            "Code tokenizer returned an incorrect first token type "
                                                    + codeBlocks.get(0).getType());
                            }
                        }

                        endOfLastBlock = cursor + 1;
                        blockStartFound = false;
                    }
                }
            }
        }

        // If there is something left after the last block, capture it as a TextBlock
        if (endOfLastBlock < text.length()) {
            blocks.add(new TextBlock(text, endOfLastBlock, text.length()));
        }

        return Collections.unmodifiableList(blocks);
    }

    /*
    #region private ================================================================================

    private readonly ILogger _log;
     */
    private final CodeTokenizer codeTokenizer = new CodeTokenizer();

    private static String subStr(String text, int startIndex, int stopIndex) {
        return text.substring(startIndex, stopIndex);
    }

    private static boolean isQuote(char c) {
        return c == Symbols.DblQuote || c == Symbols.SglQuote;
    }

    private static boolean canBeEscaped(char c) {
        return c == Symbols.DblQuote || c == Symbols.SglQuote || c == Symbols.EscapeChar;
    }
}
