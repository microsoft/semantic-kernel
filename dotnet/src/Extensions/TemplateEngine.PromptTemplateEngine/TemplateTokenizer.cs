// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.TemplateEngine.Prompt.Blocks;

namespace Microsoft.SemanticKernel.TemplateEngine.Prompt;

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
/// [template]       ::= "" | [variable] " " [template] | [value] " " [template] | [function-call] " " [template]
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
internal sealed class TemplateTokenizer
{
    /// <summary>
    /// Create a new instance of SK tokenizer
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public TemplateTokenizer(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._codeTokenizer = new CodeTokenizer(loggerFactory);
    }

    /// <summary>
    /// Extract blocks from the given text
    /// </summary>
    /// <param name="text">Text to parse</param>
    /// <returns>List of blocks found in the text</returns>
    public IList<Block> Tokenize(string? text)
    {
        // An empty block consists of 4 chars: "{{}}"
        const int EmptyCodeBlockLength = 4;
        // A block shorter than 5 chars is either empty or invalid, e.g. "{{ }}" and "{{$}}"
        const int MinCodeBlockLength = EmptyCodeBlockLength + 1;

        // Render NULL to ""
        if (string.IsNullOrEmpty(text))
        {
            return new List<Block> { new TextBlock(string.Empty, this._loggerFactory) };
        }

        // If the template is "empty" return the content as a text block
        if (text!.Length < MinCodeBlockLength)
        {
            return new List<Block> { new TextBlock(text, this._loggerFactory) };
        }

        var blocks = new List<Block>();

        var endOfLastBlock = 0;

        var blockStartPos = 0;
        var blockStartFound = false;

        var insideTextValue = false;
        var textValueDelimiter = '\0';

        bool skipNextChar = false;
        char nextChar = text[0];
        for (int nextCharCursor = 1; nextCharCursor < text.Length; nextCharCursor++)
        {
            int currentCharPos = nextCharCursor - 1;
            int cursor = nextCharCursor;
            char currentChar = nextChar;
            nextChar = text[nextCharCursor];

            if (skipNextChar)
            {
                skipNextChar = false;
                continue;
            }

            // When "{{" is found outside a value
            // Note: "{{ {{x}}" => ["{{ ", "{{x}}"]
            if (!insideTextValue && currentChar == Symbols.BlockStarter && nextChar == Symbols.BlockStarter)
            {
                // A block starts at the first "{"
                blockStartPos = currentCharPos;
                blockStartFound = true;
            }

            // After having found '{{'
            if (blockStartFound)
            {
                // While inside a text value, when the end quote is found
                if (insideTextValue)
                {
                    if (currentChar == Symbols.EscapeChar && CanBeEscaped(nextChar))
                    {
                        skipNextChar = true;
                        continue;
                    }

                    if (currentChar == textValueDelimiter)
                    {
                        insideTextValue = false;
                    }
                }
                else
                {
                    // A value starts here
                    if (IsQuote(currentChar))
                    {
                        insideTextValue = true;
                        textValueDelimiter = currentChar;
                    }
                    // If the block ends here
                    else if (currentChar == Symbols.BlockEnder && nextChar == Symbols.BlockEnder)
                    {
                        // If there is plain text between the current var/val/code block and the previous one, capture that as a TextBlock
                        if (blockStartPos > endOfLastBlock)
                        {
                            blocks.Add(new TextBlock(text, endOfLastBlock, blockStartPos, this._loggerFactory));
                        }

                        // Extract raw block
                        var contentWithDelimiters = SubStr(text, blockStartPos, cursor + 1);

                        // Remove "{{" and "}}" delimiters and trim empty chars
                        var contentWithoutDelimiters = contentWithDelimiters
                            .Substring(2, contentWithDelimiters.Length - EmptyCodeBlockLength)
                            .Trim();

                        if (contentWithoutDelimiters.Length == 0)
                        {
                            // If what is left is empty, consider the raw block a Text Block
                            blocks.Add(new TextBlock(contentWithDelimiters, this._loggerFactory));
                        }
                        else
                        {
                            List<Block> codeBlocks = this._codeTokenizer.Tokenize(contentWithoutDelimiters);

                            switch (codeBlocks[0].Type)
                            {
                                case BlockTypes.Variable:
                                    if (codeBlocks.Count > 1)
                                    {
                                        throw new SKException($"Invalid token detected after the variable: {contentWithoutDelimiters}");
                                    }

                                    blocks.Add(codeBlocks[0]);
                                    break;

                                case BlockTypes.Value:
                                    if (codeBlocks.Count > 1)
                                    {
                                        throw new SKException($"Invalid token detected after the value: {contentWithoutDelimiters}");
                                    }

                                    blocks.Add(codeBlocks[0]);
                                    break;

                                case BlockTypes.FunctionId:
                                    if (codeBlocks.Count > 2)
                                    {
                                        throw new SKException($"Functions support only one parameter: {contentWithoutDelimiters}");
                                    }

                                    blocks.Add(new CodeBlock(codeBlocks, contentWithoutDelimiters, this._loggerFactory));
                                    break;

                                case BlockTypes.Code:
                                case BlockTypes.Text:
                                case BlockTypes.Undefined:
                                default:
                                    throw new SKException($"Code tokenizer returned an incorrect first token type {codeBlocks[0].Type:G}");
                            }
                        }

                        endOfLastBlock = cursor + 1;
                        blockStartFound = false;
                    }
                }
            }
        }

        // If there is something left after the last block, capture it as a TextBlock
        if (endOfLastBlock < text.Length)
        {
            blocks.Add(new TextBlock(text, endOfLastBlock, text.Length, this._loggerFactory));
        }

        return blocks;
    }

    #region private ================================================================================

    private readonly ILoggerFactory _loggerFactory;
    private readonly CodeTokenizer _codeTokenizer;

    private static string SubStr(string text, int startIndex, int stopIndex)
    {
        return text.Substring(startIndex, stopIndex - startIndex);
    }

    private static bool IsQuote(char c)
    {
        return c is Symbols.DblQuote or Symbols.SglQuote;
    }

    private static bool CanBeEscaped(char c)
    {
        return c is Symbols.DblQuote or Symbols.SglQuote or Symbols.EscapeChar;
    }

    #endregion
}
