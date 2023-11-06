// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine;

import com.microsoft.semantickernel.templateengine.blocks.*;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

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
public class CodeTokenizer {
    private enum TokenTypes {
        None(0),
        Value(1),
        Variable(2),
        FunctionId(3);

        TokenTypes(int i) {}
    }

    public CodeTokenizer() {}

    /// <summary>
    /// Tokenize a code block, without checking for syntax errors
    /// </summary>
    /// <param name="text">Text to parse</param>
    /// <returns>A list of blocks</returns>
    public List<Block> tokenize(String text) {
        if (text == null) {
            return new ArrayList<>();
        }

        // Remove spaces, which are ignored anyway
        text = text.trim();

        // Render NULL to ""
        if (text.isEmpty()) {
            return Collections.unmodifiableList(new ArrayList<>());
        }

        // Track what type of token we're reading
        TokenTypes currentTokenType = TokenTypes.None;

        // Track the content of the current token
        StringBuilder currentTokenContent = new StringBuilder();

        char textValueDelimiter = '\0';

        List<Block> blocks = new ArrayList<>();
        char nextChar = text.charAt(0);

        // Tokens must be separated by spaces, track their presence
        boolean spaceSeparatorFound = false;

        // 1 char only edge case
        if (text.length() == 1) {
            switch (nextChar) {
                case Symbols.VarPrefix:
                    blocks.add(new VarBlock(text));
                    break;

                case Symbols.DblQuote:
                case Symbols.SglQuote:
                    blocks.add(new ValBlock(text));
                    break;

                default:
                    blocks.add(new FunctionIdBlock(text));
                    break;
            }

            return blocks;
        }

        boolean skipNextChar = false;
        for (int nextCharCursor = 1; nextCharCursor < text.length(); nextCharCursor++) {
            char currentChar = nextChar;
            nextChar = text.charAt(nextCharCursor);

            if (skipNextChar) {
                skipNextChar = false;
                continue;
            }

            // First char is easy
            if (nextCharCursor == 1) {
                if (isVarPrefix(currentChar)) {
                    currentTokenType = TokenTypes.Variable;
                } else if (isQuote(currentChar)) {
                    currentTokenType = TokenTypes.Value;
                    textValueDelimiter = currentChar;
                } else {
                    currentTokenType = TokenTypes.FunctionId;
                }

                currentTokenContent.append(currentChar);
                continue;
            }

            // While reading a values between quotes
            if (currentTokenType == TokenTypes.Value) {
                // If the current char is escaping the next special char:
                // - skip the current char (escape char)
                // - add the next (special char)
                // - jump to the one after (to handle "\\" properly)
                if (currentChar == Symbols.EscapeChar && CanBeEscaped(nextChar)) {
                    currentTokenContent.append(nextChar);
                    skipNextChar = true;
                    continue;
                }

                currentTokenContent.append(currentChar);

                // When we reach the end of the value
                if (currentChar == textValueDelimiter) {
                    blocks.add(new ValBlock(currentTokenContent.toString()));
                    currentTokenContent = new StringBuilder();
                    currentTokenType = TokenTypes.None;
                    spaceSeparatorFound = false;
                }

                continue;
            }

            // If we're not between quotes, a space signals the end of the current token
            // Note: there might be multiple consecutive spaces
            if (IsBlankSpace(currentChar)) {
                if (currentTokenType == TokenTypes.Variable) {
                    blocks.add(new VarBlock(currentTokenContent.toString()));
                    currentTokenContent = new StringBuilder();
                } else if (currentTokenType == TokenTypes.FunctionId) {
                    blocks.add(new FunctionIdBlock(currentTokenContent.toString()));
                    currentTokenContent = new StringBuilder();
                }

                spaceSeparatorFound = true;
                currentTokenType = TokenTypes.None;

                continue;
            }

            // If we're not inside a quoted value and we're not processing a space
            currentTokenContent.append(currentChar);

            if (currentTokenType == TokenTypes.None) {
                if (!spaceSeparatorFound) {
                    throw new TemplateException(
                            TemplateException.ErrorCodes.SYNTAX_ERROR,
                            "Tokens must be separated by one space least");
                }

                if (isQuote(currentChar)) {
                    // A quoted value starts here
                    currentTokenType = TokenTypes.Value;
                    textValueDelimiter = currentChar;
                } else if (isVarPrefix(currentChar)) {
                    // A variable starts here
                    currentTokenType = TokenTypes.Variable;
                } else {
                    // A function Id starts here
                    currentTokenType = TokenTypes.FunctionId;
                }
            }
        }

        // Capture last token
        currentTokenContent.append(nextChar);
        switch (currentTokenType) {
            case Value:
                blocks.add(new ValBlock(currentTokenContent.toString()));
                break;

            case Variable:
                blocks.add(new VarBlock(currentTokenContent.toString()));
                break;

            case FunctionId:
                blocks.add(new FunctionIdBlock(currentTokenContent.toString()));
                break;

            case None:
                throw new TemplateException(
                        TemplateException.ErrorCodes.SYNTAX_ERROR,
                        "Tokens must be separated by one space least");
        }

        return blocks;
    }

    private static boolean isVarPrefix(char c) {
        return (c == Symbols.VarPrefix);
    }

    private static boolean IsBlankSpace(char c) {
        return Character.isWhitespace(c);
    }

    private static boolean isQuote(char c) {
        return c == Symbols.DblQuote || c == Symbols.SglQuote;
    }

    private static boolean CanBeEscaped(char c) {
        return c == Symbols.DblQuote || c == Symbols.SglQuote || c == Symbols.EscapeChar;
    }
}
