// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.semantickernel;

import com.microsoft.semantickernel.Verify;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.Block;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.FunctionIdBlock;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.NamedArgBlock;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.Symbols;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.ValBlock;
import com.microsoft.semantickernel.templateengine.semantickernel.blocks.VarBlock;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.annotation.Nullable;

/**
 * Simple tokenizer used for default SK template code language.
 *
 * BNF parsed by TemplateTokenizer:
 * [template]       ::= "" | [block] | [block] [template]
 * [block]          ::= [sk-block] | [text-block]
 * [sk-block]       ::= "{{" [variable] "}}" | "{{" [value] "}}" | "{{" [function-call] "}}"
 * [text-block]     ::= [any-char] | [any-char] [text-block]
 * [any-char]       ::= any char
 *
 * BNF parsed by CodeTokenizer:
 * [template]       ::= "" | [variable] " " [template] | [value] " " [template] | [function-call] "
 * [variable]       ::= "$" [valid-name]
 * [value]          ::= "'" [text] "'" | '"' [text] '"'
 * [function-call]  ::= [function-id] | [function-id] [parameter]
 * [parameter]      ::= [variable] | [value]
 *
 * BNF parsed by dedicated blocks
 * [function-id]    ::= [valid-name] | [valid-name] "." [valid-name]
 * [valid-name]     ::= [valid-symbol] | [valid-symbol] [valid-name]
 * [valid-symbol]   ::= [letter] | [digit] | "_"
 * [letter]         ::= "a" | "b" ... | "z" | "A" | "B" ... | "Z"
 * [digit]          ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
 */
public class CodeTokenizer {

    private enum TokenTypes {
        None(0),
        Value(1),
        Variable(2),
        FunctionId(3),
        NamedArg(4);

        TokenTypes(int i) {
        }
    }

    /**
     * Initializes a new instance of the {@link CodeTokenizer} class.
     */
    public CodeTokenizer() {
    }

    /**
     * Tokenize a code block, without checking for syntax errors
     * @param text Text to parse
     * @return A list of blocks
     */
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

        // Named args may contain string values that contain spaces. These are used
        // to determine when a space occurs between quotes.
        boolean namedArgSeparatorFound = false;
        char namedArgValuePrefix = '\0';

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
                    // A function Id starts here
                    currentTokenType = TokenTypes.FunctionId;
                }

                currentTokenContent.append(currentChar);
                continue;
            }

            // While reading a values between quotes
            if (currentTokenType == TokenTypes.Value
                || (currentTokenType == TokenTypes.NamedArg && isQuote(namedArgValuePrefix))) {
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
                } else if (currentChar == namedArgValuePrefix
                    && currentTokenType == TokenTypes.NamedArg) {
                    blocks.add(NamedArgBlock.from(currentTokenContent.toString()));
                    currentTokenContent = new StringBuilder();
                    currentTokenType = TokenTypes.None;
                    spaceSeparatorFound = false;
                    namedArgSeparatorFound = false;
                    namedArgValuePrefix = '\0';
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
                    String tokenContent = currentTokenContent.toString();
                    // This isn't an expected block at this point but the TemplateTokenizer should throw an error when
                    // a named arg is used without a function call

                    NamedArgBlock namedArg = getNamedArg(tokenContent);

                    if (namedArg != null) {
                        blocks.add(namedArg);
                    } else {
                        blocks.add(new FunctionIdBlock(tokenContent));
                    }
                    currentTokenContent = new StringBuilder();
                    currentTokenType = TokenTypes.None;
                } else if (currentTokenType == TokenTypes.NamedArg && namedArgSeparatorFound
                    && namedArgValuePrefix != 0) {
                    blocks.add(
                        NamedArgBlock.from(currentTokenContent.toString()));
                    currentTokenContent = new StringBuilder();
                    namedArgSeparatorFound = false;
                    namedArgValuePrefix = '\0';
                    currentTokenType = TokenTypes.None;
                }
                spaceSeparatorFound = true;
                currentTokenType = TokenTypes.None;

                continue;
            }

            // If reading a named argument and either the '=' or the value prefix ($, ', or ") haven't been found
            if (currentTokenType == TokenTypes.NamedArg && (!namedArgSeparatorFound
                || namedArgValuePrefix == 0)) {
                if (!namedArgSeparatorFound) {
                    if (currentChar == Symbols.NamedArgBlockSeparator) {
                        namedArgSeparatorFound = true;
                    }
                } else {
                    namedArgValuePrefix = currentChar;
                    if (!isQuote(namedArgValuePrefix) && namedArgValuePrefix != Symbols.VarPrefix) {
                        throw new SKException(
                            "Named argument values need to be prefixed with a quote or "
                                + Symbols.VarPrefix);
                    }
                }
                currentTokenContent.append(currentChar);
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
                } else if (blocks.isEmpty()) {
                    // A function Id starts here
                    currentTokenType = TokenTypes.FunctionId;
                } else {
                    // A named arg starts here
                    currentTokenType = TokenTypes.NamedArg;
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
                NamedArgBlock namedArg = getNamedArg(currentTokenContent.toString());

                // This isn't an expected block at this point but the TemplateTokenizer should throw an error when
                // a named arg is used without a function call
                if (namedArg != null) {
                    blocks.add(namedArg);
                } else {
                    blocks.add(new FunctionIdBlock(currentTokenContent.toString()));
                }

                break;
            case NamedArg:
                blocks.add(NamedArgBlock.from(currentTokenContent.toString()));
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

    @SuppressWarnings("NullAway")
    @Nullable
    private static NamedArgBlock getNamedArg(String tokenContent) {

        String name = NamedArgBlock.tryGetName(tokenContent);
        String value = NamedArgBlock.tryGetValue(tokenContent);

        if (Verify.isNullOrEmpty(name) || Verify.isNullOrEmpty(value)) {
            return null;
        }
        NamedArgBlock block = new NamedArgBlock(tokenContent, name, value);
        if (block.isValid()) {
            return block;
        }

        return null;
    }
}
