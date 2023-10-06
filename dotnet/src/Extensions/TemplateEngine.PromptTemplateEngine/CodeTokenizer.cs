// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.TemplateEngine.Prompt.Blocks;

namespace Microsoft.SemanticKernel.TemplateEngine.Prompt;

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
        NamedArg = 4,
    }

    private readonly ILoggerFactory _loggerFactory;

    public CodeTokenizer(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
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
        if (string.IsNullOrEmpty(text)) { return new List<Block>(); }

        // Track what type of token we're reading
        TokenTypes currentTokenType = TokenTypes.None;

        // Track the content of the current token
        var currentTokenContent = new StringBuilder();

        char textValueDelimiter = '\0';

        var blocks = new List<Block>();
        char nextChar = text![0];

        // Tokens must be separated by spaces, track their presence
        bool spaceSeparatorFound = false;

        // Named args may contain string values that contain spaces. These are used
        // to determine when a space occurs between quotes.
        bool namedArgSeparatorFound = false;
        char namedArgValuePrefix = '\0';

        // 1 char only edge case
        if (text.Length == 1)
        {
            if (Symbols.IsVarPrefix(nextChar))
            {
                blocks.Add(new VarBlock(text, this._loggerFactory));
            }
            else if (Symbols.IsQuote(nextChar))
            {
                blocks.Add(new ValBlock(text, this._loggerFactory));
            }
            else
            {
                blocks.Add(new FunctionIdBlock(text, this._loggerFactory));
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
                if (Symbols.IsVarPrefix(currentChar))
                {
                    currentTokenType = TokenTypes.Variable;
                }
                else if (Symbols.IsQuote(currentChar))
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
            if (currentTokenType == TokenTypes.Value || (currentTokenType == TokenTypes.NamedArg && Symbols.IsQuote(namedArgValuePrefix)))
            {
                // If the current char is escaping the next special char:
                // - skip the current char (escape char)
                // - add the next (special char)
                // - jump to the one after (to handle "\\" properly)
                if (currentChar == Symbols.EscapeChar && Symbols.CanBeEscaped(nextChar))
                {
                    currentTokenContent.Append(nextChar);
                    skipNextChar = true;
                    continue;
                }

                currentTokenContent.Append(currentChar);

                // When we reach the end of the value
                if (currentChar == textValueDelimiter && currentTokenType == TokenTypes.Value)
                {
                    blocks.Add(new ValBlock(currentTokenContent.ToString(), this._loggerFactory));
                    currentTokenContent.Clear();
                    currentTokenType = TokenTypes.None;
                    spaceSeparatorFound = false;
                }
                else if (currentChar == namedArgValuePrefix && currentTokenType == TokenTypes.NamedArg)
                {
                    blocks.Add(new NamedArgBlock(currentTokenContent.ToString(), this._loggerFactory));
                    currentTokenContent.Clear();
                    currentTokenType = TokenTypes.None;
                    spaceSeparatorFound = false;
                    namedArgSeparatorFound = false;
                    namedArgValuePrefix = '\0';
                }

                continue;
            }

            // If we're not between quotes, a space signals the end of the current token
            // Note: there might be multiple consecutive spaces
            if (Symbols.IsBlankSpace(currentChar))
            {
                if (currentTokenType == TokenTypes.Variable)
                {
                    blocks.Add(new VarBlock(currentTokenContent.ToString(), this._loggerFactory));
                    currentTokenContent.Clear();
                    currentTokenType = TokenTypes.None;
                }
                else if (currentTokenType == TokenTypes.FunctionId)
                {
                    var tokenContent = currentTokenContent.ToString();
                    // This isn't an expected block at this point but the TemplateTokenizer should throw an error when
                    // a named arg is used without a function call
                    if (CodeTokenizer.IsValidNamedArg(tokenContent))
                    {
                        blocks.Add(new NamedArgBlock(tokenContent, this._loggerFactory));
                    }
                    else
                    {
                        blocks.Add(new FunctionIdBlock(tokenContent, this._loggerFactory));
                    }
                    currentTokenContent.Clear();
                    currentTokenType = TokenTypes.None;
                }
                else if (currentTokenType == TokenTypes.NamedArg && namedArgSeparatorFound && namedArgValuePrefix != 0)
                {
                    blocks.Add(new NamedArgBlock(currentTokenContent.ToString(), this._loggerFactory));
                    currentTokenContent.Clear();
                    namedArgSeparatorFound = false;
                    namedArgValuePrefix = '\0';
                    currentTokenType = TokenTypes.None;
                }

                spaceSeparatorFound = true;

                continue;
            }

            // If reading a named argument and either the '=' or the value prefix ($, ', or ") haven't been found
            if (currentTokenType == TokenTypes.NamedArg && (!namedArgSeparatorFound || namedArgValuePrefix == 0))
            {
                if (!namedArgSeparatorFound)
                {
                    if (currentChar == Symbols.NamedArgBlockSeparator)
                    {
                        namedArgSeparatorFound = true;
                    }
                }
                else
                {
                    namedArgValuePrefix = currentChar;
                    if (!Symbols.IsQuote((char)namedArgValuePrefix) && !Symbols.IsVarPrefix((char)namedArgValuePrefix))
                    {
                        throw new SKException($"Named argument values need to be prefixed with a quote or {Symbols.VarPrefix}.");
                    }
                }
                currentTokenContent.Append(currentChar);
                continue;
            }

            // If we're not inside a quoted value and we're not processing a space
            currentTokenContent.Append(currentChar);

            if (currentTokenType == TokenTypes.None)
            {
                if (!spaceSeparatorFound)
                {
                    throw new SKException("Tokens must be separated by one space least");
                }

                if (Symbols.IsQuote(currentChar))
                {
                    // A quoted value starts here
                    currentTokenType = TokenTypes.Value;
                    textValueDelimiter = currentChar;
                }
                else if (Symbols.IsVarPrefix(currentChar))
                {
                    // A variable starts here
                    currentTokenType = TokenTypes.Variable;
                }
                else if (blocks.Count == 0)
                {
                    // A function Id starts here
                    currentTokenType = TokenTypes.FunctionId;
                }
                else
                {
                    // A named arg starts here
                    currentTokenType = TokenTypes.NamedArg;
                }
            }
        }

        // Capture last token
        currentTokenContent.Append(nextChar);
        switch (currentTokenType)
        {
            case TokenTypes.Value:
                blocks.Add(new ValBlock(currentTokenContent.ToString(), this._loggerFactory));
                break;

            case TokenTypes.Variable:
                blocks.Add(new VarBlock(currentTokenContent.ToString(), this._loggerFactory));
                break;

            case TokenTypes.FunctionId:
                var tokenContent = currentTokenContent.ToString();
                // This isn't an expected block at this point but the TemplateTokenizer should throw an error when
                // a named arg is used without a function call
                if (CodeTokenizer.IsValidNamedArg(tokenContent))
                {
                    blocks.Add(new NamedArgBlock(tokenContent, this._loggerFactory));
                }
                else
                {
                    blocks.Add(new FunctionIdBlock(currentTokenContent.ToString(), this._loggerFactory));
                }
                break;

            case TokenTypes.NamedArg:
                blocks.Add(new NamedArgBlock(currentTokenContent.ToString(), this._loggerFactory));
                break;

            case TokenTypes.None:
                throw new SKException("Tokens must be separated by one space least");
        }

        return blocks;
    }

    [SuppressMessage("Design", "CA1031:Modify to catch a more specific allowed exception type, or rethrow exception",
    Justification = "Does not throw an exception by design.")]
    private static bool IsValidNamedArg(string tokenContent)
    {
        try
        {
            var tokenContentAsNamedArg = new NamedArgBlock(tokenContent);
            return tokenContentAsNamedArg.IsValid(out var error);
        }
        catch
        {
            return false;
        }
    }
}
