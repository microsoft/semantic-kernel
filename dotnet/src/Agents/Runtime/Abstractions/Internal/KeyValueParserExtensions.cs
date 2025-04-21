// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Agents.Runtime.Internal;

/// <summary>
/// Provides helper methods for parsing key-value string representations.
/// </summary>
internal static class KeyValueParserExtensions
{
    /// <summary>
    /// The regular expression pattern used to match key-value pairs in the format "key/value".
    /// </summary>
    private const string KVPairPattern = @"^(?<key>\w+)/(?<value>\w+)$";

    /// <summary>
    /// The compiled regex used for extracting key-value pairs from a string.
    /// </summary>
    private static readonly Regex KVPairRegex = new(KVPairPattern, RegexOptions.Compiled);

    /// <summary>
    /// Parses a string in the format "key/value" into a tuple containing the key and value.
    /// </summary>
    /// <param name="inputPair">The input string containing a key-value pair.</param>
    /// <param name="keyName">The expected name of the key component.</param>
    /// <param name="valueName">The expected name of the value component.</param>
    /// <returns>A tuple containing the extracted key and value.</returns>
    /// <exception cref="FormatException">
    /// Thrown if the input string does not match the expected "key/value" format.
    /// </exception>
    /// <example>
    /// Example usage:
    /// <code>
    /// string input = "agent1/12345";
    /// var result = input.ToKVPair("Type", "Key");
    /// Console.WriteLine(result.Item1); // Outputs: agent1
    /// Console.WriteLine(result.Item2); // Outputs: 12345
    /// </code>
    /// </example>
    public static (string, string) ToKeyValuePair(this string inputPair, string keyName, string valueName)
    {
        Match match = KVPairRegex.Match(inputPair);
        if (match.Success)
        {
            return (match.Groups["key"].Value, match.Groups["value"].Value);
        }

        throw new FormatException($"Invalid key-value pair format: {inputPair}; expecting \"{{{keyName}}}/{{{valueName}}}\"");
    }
}
