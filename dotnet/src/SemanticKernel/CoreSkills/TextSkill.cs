// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.CoreSkills;

/// <summary>
/// TextSkill provides a set of functions to manipulate strings.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("text", new TextSkill());
///
/// Examples:
/// SKContext["input"] = "  hello world  "
/// {{text.trim $input}} => "hello world"
/// {{text.trimStart $input} => "hello world  "
/// {{text.trimEnd $input} => "  hello world"
/// SKContext["input"] = "hello world"
/// {{text.uppercase $input}} => "HELLO WORLD"
/// SKContext["input"] = "HELLO WORLD"
/// {{text.lowercase $input}} => "hello world"
/// </example>
public class TextSkill
{
    /// <summary>
    /// Trim whitespace from the start and end of a string.
    /// </summary>
    /// <example>
    /// SKContext["input"] = "  hello world  "
    /// {{text.trim $input}} => "hello world"
    /// </example>
    /// <param name="text"> The string to trim. </param>
    /// <returns> The trimmed string. </returns>
    [SKFunction("Trim whitespace from the start and end of a string.")]
    public string Trim(string text)
    {
        return text.Trim();
    }

    /// <summary>
    /// Trim whitespace from the start of a string.
    /// </summary>
    /// <example>
    /// SKContext["input"] = "  hello world  "
    /// {{text.trimStart $input} => "hello world  "
    /// </example>
    /// <param name="text"> The string to trim. </param>
    /// <returns> The trimmed string. </returns>
    [SKFunction("Trim whitespace from the start of a string.")]
    public string TrimStart(string text)
    {
        return text.TrimStart();
    }

    /// <summary>
    /// Trim whitespace from the end of a string.
    /// </summary>
    /// <example>
    /// SKContext["input"] = "  hello world  "
    /// {{text.trimEnd $input} => "  hello world"
    /// </example>
    /// <param name="text"> The string to trim. </param>
    /// <returns> The trimmed string. </returns>
    [SKFunction("Trim whitespace from the end of a string.")]
    public string TrimEnd(string text)
    {
        return text.TrimEnd();
    }

    /// <summary>
    /// Convert a string to uppercase.
    /// </summary>
    /// <example>
    /// SKContext["input"] = "hello world"
    /// {{text.uppercase $input}} => "HELLO WORLD"
    /// </example>
    /// <param name="text"> The string to convert. </param>
    /// <returns> The converted string. </returns>
    [SKFunction("Convert a string to uppercase.")]
    public string Uppercase(string text)
    {
        return text.ToUpper(System.Globalization.CultureInfo.CurrentCulture);
    }

    /// <summary>
    /// Convert a string to lowercase.
    /// </summary>
    /// <example>
    /// SKContext["input"] = "HELLO WORLD"
    /// {{text.lowercase $input}} => "hello world"
    /// </example>
    /// <param name="text"> The string to convert. </param>
    /// <returns> The converted string. </returns>
    [SKFunction("Convert a string to lowercase.")]
    public string Lowercase(string text)
    {
        return text.ToLower(System.Globalization.CultureInfo.CurrentCulture);
    }

    /// <summary>
    /// Get the length of a string. Returns 0 if null or empty
    /// </summary>
    /// <example>
    /// SKContext["input"] = "HELLO WORLD"
    /// {{text.length $input}} => "11"
    /// </example>
    /// <param name="text"> The string to get length. </param>
    /// <returns>The length size of string (0) if null or empty.</returns>
    [SKFunction("Get the length of a string.")]
    public string Length(string text)
    {
        return (text?.Length ?? 0).ToString(System.Globalization.CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Concatenate two strings into one
    /// </summary>
    /// <example>
    /// text = "HELLO "
    /// SKContext["input2"] = "WORLD"
    /// Result: "HELLO WORLD"
    /// </example>
    /// <param name="text"> The string to get length. </param>
    /// <param name="context">Context where the input2 value will be retrieved</param>
    /// <returns>Concatenation result from both inputs.</returns>
    [SKFunction("Concat two strings into one.")]
    [SKFunctionInput(Description = "First input to concatenate with")]
    [SKFunctionContextParameter(Name = "input2", Description = "Second input to concatenate with")]
    public string Concat(string text, SKContext context)
    {
        return string.Concat(text, context["input2"]);
    }

    [SKFunction("Echo the input string. Useful for capturing plan input for use in multiple functions.")]
    [SKFunctionInput(Description = "Input string to echo.")]
    public string Echo(string text)
    {
        return text;
    }
}
