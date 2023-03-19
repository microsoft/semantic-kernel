// Copyright (c) Microsoft. All rights reserved.

/**
 * TextSkill provides a set of functions to manipulate strings.
 *
 * Usage: kernel.ImportSkill("text", new TextSkill());
 * Examples:
 * SKContext["input"] = "  hello world  "
 * {{text.trim $input}} => "hello world"
 * {{text.trimStart $input} => "hello world  "
 * {{text.trimEnd $input} => "  hello world"
 * SKContext["input"] = "hello world"
 * {{text.uppercase $input}} => "HELLO WORLD"
 * SKContext["input"] = "HELLO WORLD"
 * {{text.lowercase $input}} => "hello world"
 */
export class TextSkill {
    /**
     * Trim whitespace from the start and end of a string.
     *
     * Examples:
     * SKContext["input"] = "  hello world  "
     * {{text.trim $input}} => "hello world"
     *
     * @param text The string to trim.
     * @returns The trimmed string.
     */
    public trim(text: string): string {
        return text.trim();
    }

    /**
     * Trim whitespace from the start of a string.
     *
     * Examples:
     * SKContext["input"] = "  hello world  "
     * {{text.trimStart $input} => "hello world  "
     *
     * @param text The string to trim.
     * @returns The trimmed string.
     */
    public trimStart(text: string): string {
        return text.trimStart();
    }

    /**
     * Trim whitespace from the end of a string.
     *
     * Examples:
     * SKContext["input"] = "  hello world  "
     * {{text.trimEnd $input} => "  hello world"
     *
     * @param text The string to trim.
     * @returns The trimmed string.
     */
    public trimEnd(text: string): string {
        return text.trimEnd();
    }

    /**
     * Convert a string to uppercase.
     *
     * Examples:
     * SKContext["input"] = "hello world"
     * {{text.uppercase $input}} => "HELLO WORLD"
     *
     * @param text The string to convert.
     * @returns The converted string.
     */
    public uppercase(text: string): string {
        return text.toUpperCase();
    }

    /**
     * Convert a string to lowercase.
     *
     * Examples:
     * SKContext["input"] = "HELLO WORLD"
     * {{text.lowercase $input}} => "hello world"
     *
     * @param text The string to convert.
     * @returns The converted string.
     */
    public lowercase(text: string): string {
        return text.toLowerCase();
    }
}
