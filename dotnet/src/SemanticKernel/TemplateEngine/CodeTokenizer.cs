// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Simple tokenizer used for default SK template code language.
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
internal sealed class CodeTokenizer
{
    private enum TokenTypes
    {
        None = 0,
        Value = 1,
        Variable = 2,
        FunctionId = 3,
    }

    private readonly ILogger _logger;

    public CodeTokenizer(ILogger? logger = null)
    {
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <summary>
    /// Tokenize a code block, without checking for syntax errors
    /// </summary>
    /// <param name="text">Text to parse</param>
    /// <returns>A list of blocks</returns>
    public List<Block> Tokenize(string? text)
    {
        // Remove spaces, which are ignored anyway
        text = text?.Trim();

        // Render NULL to ""
        if (text.IsNullOrEmpty()) { return new List<Block>(); }

        // Track what type of token we're reading
        TokenTypes currentTokenType = TokenTypes.None;

        // Track the content of the current token
        var currentTokenContent = new StringBuilder();

        char textValueDelimiter = '\0';

        var blocks = new List<Block>();
        char nextChar = text[0];

        // Tokens must be separated by spaces, track their presence
        bool spaceSeparatorFound = false;

        // 1 char only edge case
        if (text.Length == 1)
        {
            switch (nextChar)
            {
                case Symbols.VarPrefix:
                    blocks.Add(new VarBlock(text, this._logger));
                    break;

                case Symbols.DblQuote:
                case Symbols.SglQuote:
                    blocks.Add(new ValBlock(text, this._logger));
                    break;

                default:
                    blocks.Add(new FunctionIdBlock(text, this._logger));
                    break;
            }

            return blocks;
        }

        bool skipNextChar = false;
        for (int nextCharCursor = 1; nextCharCursor < text.Length; nextCharCursor++)
        {
            char currentChar = nextChar;
            nextChar = text[nextCharCursor];

            if (skipNextChar)
            {
                skipNextChar = false;
                continue;
            }

            // First char is easy
            if (nextCharCursor == 1)
            {
                if (IsVarPrefix(currentChar))
                {
                    currentTokenType = TokenTypes.Variable;
                }
                else if (IsQuote(currentChar))
                {
                    currentTokenType = TokenTypes.Value;
                    textValueDelimiter = currentChar;
                }
                else
                {
                    currentTokenType = TokenTypes.FunctionId;
                }

                currentTokenContent.Append(currentChar);
                continue;
            }

            // While reading a values between quotes
            if (currentTokenType == TokenTypes.Value)
            {
                // If the current char is escaping the next special char:
                // - skip the current char (escape char)
                // - add the next (special char)
                // - jump to the one after (to handle "\\" properly)
                if (currentChar == Symbols.EscapeChar && CanBeEscaped(nextChar))
                {
                    currentTokenContent.Append(nextChar);
                    skipNextChar = true;
                    continue;
                }

                currentTokenContent.Append(currentChar);

                // When we reach the end of the value
                if (currentChar == textValueDelimiter)
                {
                    blocks.Add(new ValBlock(currentTokenContent.ToString(), this._logger));
                    currentTokenContent.Clear();
                    currentTokenType = TokenTypes.None;
                    spaceSeparatorFound = false;
                }

                continue;
            }

            // If we're not between quotes, a space signals the end of the current token
            // Note: there might be multiple consecutive spaces
            if (IsBlankSpace(currentChar))
            {
                if (currentTokenType == TokenTypes.Variable)
                {
                    blocks.Add(new VarBlock(currentTokenContent.ToString(), this._logger));
                    currentTokenContent.Clear();
                }
                else if (currentTokenType == TokenTypes.FunctionId)
                {
                    blocks.Add(new FunctionIdBlock(currentTokenContent.ToString(), this._logger));
                    currentTokenContent.Clear();
                }

                spaceSeparatorFound = true;
                currentTokenType = TokenTypes.None;

                continue;
            }

            // If we're not inside a quoted value and we're not processing a space
            currentTokenContent.Append(currentChar);

            if (currentTokenType == TokenTypes.None)
            {
                if (!spaceSeparatorFound)
                {
                    throw new TemplateException(TemplateException.ErrorCodes.SyntaxError,
                        "Tokens must be separated by one space least");
                }

                if (IsQuote(currentChar))
                {
                    // A quoted value starts here
                    currentTokenType = TokenTypes.Value;
                    textValueDelimiter = currentChar;
                }
                else if (IsVarPrefix(currentChar))
                {
                    // A variable starts here
                    currentTokenType = TokenTypes.Variable;
                }
                else
                {
                    // A function Id starts here
                    currentTokenType = TokenTypes.FunctionId;
                }
            }
        }

        // Capture last token
        currentTokenContent.Append(nextChar);
        switch (currentTokenType)
        {
            case TokenTypes.Value:
                blocks.Add(new ValBlock(currentTokenContent.ToString(), this._logger));
                break;

            case TokenTypes.Variable:
                blocks.Add(new VarBlock(currentTokenContent.ToString(), this._logger));
                break;

            case TokenTypes.FunctionId:
                blocks.Add(new FunctionIdBlock(currentTokenContent.ToString(), this._logger));
                break;

            case TokenTypes.None:
                throw new TemplateException(TemplateException.ErrorCodes.SyntaxError,
                    "Tokens must be separated by one space least");
        }

        return blocks;
    }

    private static bool IsVarPrefix(char c)
    {
        return (c == Symbols.VarPrefix);
    }

    private static bool IsBlankSpace(char c)
    {
        return c is Symbols.Space or Symbols.NewLine or Symbols.CarriageReturn or Symbols.Tab;
    }

    private static bool IsQuote(char c)
    {
        return c is Symbols.DblQuote or Symbols.SglQuote;
    }

    private static bool CanBeEscaped(char c)
    {
        return c is Symbols.DblQuote or Symbols.SglQuote or Symbols.EscapeChar;
    }
}
