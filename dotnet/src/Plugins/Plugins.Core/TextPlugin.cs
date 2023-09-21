// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;

namespace Microsoft.SemanticKernel.Plugins.Core;

/// <summary>
/// TextPlugin provides a set of functions to manipulate strings.
/// </summary>
/// <example>
/// Usage: kernel.ImportPlugin("text", new TextPlugin());
///
/// Examples:
/// SKContext.Variables["input"] = "  hello world  "
/// {{text.trim $input}} => "hello world"
/// {{text.trimStart $input} => "hello world  "
/// {{text.trimEnd $input} => "  hello world"
/// SKContext.Variables["input"] = "hello world"
/// {{text.uppercase $input}} => "HELLO WORLD"
/// SKContext.Variables["input"] = "HELLO WORLD"
/// {{text.lowercase $input}} => "hello world"
/// </example>
public sealed class TextPlugin
{
    /// <summary>
    /// Trim whitespace from the start and end of a string.
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "  hello world  "
    /// {{text.trim $input}} => "hello world"
    /// </example>
    /// <param name="input"> The string to trim. </param>
    /// <returns> The trimmed string. </returns>
    [SKFunction, Description("Trim whitespace from the start and end of a string.")]
    public string Trim(string input) => input.Trim();

    /// <summary>
    /// Trim whitespace from the start of a string.
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "  hello world  "
    /// {{text.trimStart $input} => "hello world  "
    /// </example>
    /// <param name="input"> The string to trim. </param>
    /// <returns> The trimmed string. </returns>
    [SKFunction, Description("Trim whitespace from the start of a string.")]
    public string TrimStart(string input) => input.TrimStart();

    /// <summary>
    /// Trim whitespace from the end of a string.
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "  hello world  "
    /// {{text.trimEnd $input} => "  hello world"
    /// </example>
    /// <param name="input"> The string to trim. </param>
    /// <returns> The trimmed string. </returns>
    [SKFunction, Description("Trim whitespace from the end of a string.")]
    public string TrimEnd(string input) => input.TrimEnd();

    /// <summary>
    /// Convert a string to uppercase.
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "hello world"
    /// {{text.uppercase $input}} => "HELLO WORLD"
    /// </example>
    /// <param name="input"> The string to convert. </param>
    /// <param name="cultureInfo"> An object that supplies culture-specific casing rules. </param>
    /// <returns> The converted string. </returns>
    [SKFunction, Description("Convert a string to uppercase.")]
    public string Uppercase(string input, CultureInfo? cultureInfo = null) => input.ToUpper(cultureInfo);

    /// <summary>
    /// Convert a string to lowercase.
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "HELLO WORLD"
    /// {{text.lowercase $input}} => "hello world"
    /// </example>
    /// <param name="input"> The string to convert. </param>
    /// <param name="cultureInfo"> An object that supplies culture-specific casing rules. </param>
    /// <returns> The converted string. </returns>
    [SKFunction, Description("Convert a string to lowercase.")]
    public string Lowercase(string input, CultureInfo? cultureInfo = null) => input.ToLower(cultureInfo);

    /// <summary>
    /// Get the length of a string. Returns 0 if null or empty
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "HELLO WORLD"
    /// {{text.length $input}} => "11"
    /// </example>
    /// <param name="input"> The string to get length. </param>
    /// <returns>The length size of string (0) if null or empty.</returns>
    [SKFunction, Description("Get the length of a string.")]
    public int Length(string input) => input?.Length ?? 0;

    /// <summary>
    /// Concatenate two strings into one
    /// </summary>
    /// <example>
    /// text = "HELLO "
    /// SKContext.Variables["input2"] = "WORLD"
    /// Result: "HELLO WORLD"
    /// </example>
    /// <param name="input">First input to concatenate with</param>
    /// <param name="input2">Second input to concatenate with</param>
    /// <returns>Concatenation result from both inputs.</returns>
    [SKFunction, Description("Concat two strings into one.")]
    public string Concat(
        [Description("First input to concatenate with")] string input,
        [Description("Second input to concatenate with")] string input2) =>
        string.Concat(input, input2);

    /// <summary>
    /// Echo the input string. Useful for capturing plan input for use in multiple functions.
    /// </summary>
    /// <param name="text">Input string to echo.</param>
    /// <returns>The input string.</returns>
    [SKFunction, Description("Echo the input string. Useful for capturing plan input for use in multiple functions.")]
    public string Echo(
      [Description("Input string to echo.")] string text)
    {
        return text;
    }
}
