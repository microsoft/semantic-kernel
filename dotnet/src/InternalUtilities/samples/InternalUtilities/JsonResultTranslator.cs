// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using Microsoft.SemanticKernel;

namespace Resources;
/// <summary>
/// Supports parsing json from a text block that may contain literals delimiters:
/// <list type="table">
/// <item>
/// <code>
/// [json]
/// </code>
/// </item>
/// <item>
/// <code>
/// ```
/// [json]
/// ```
/// </code>
/// </item>
/// <item>
/// <code>
/// ```json
/// [json]
/// ```
/// </code>
/// </item>
/// </list>
/// </summary>
/// <remarks>
/// Encountering json with this form of delimiters is not uncommon for agent scenarios.
/// </remarks>
public static class JsonResultTranslator
{
    private const string LiteralDelimiter = "```";
    private const string JsonPrefix = "json";

    /// <summary>
    /// Utility method for extracting a JSON result from an agent response.
    /// </summary>
    /// <param name="result">A text result</param>
    /// <typeparam name="TResult">The target type of the <see cref="FunctionResult"/>.</typeparam>
    /// <returns>The JSON translated to the requested type.</returns>
    public static TResult? Translate<TResult>(string? result)
    {
        if (string.IsNullOrWhiteSpace(result))
        {
            return default;
        }

        string rawJson = ExtractJson(result);

        return JsonSerializer.Deserialize<TResult>(rawJson);
    }

    private static string ExtractJson(string result)
    {
        // Search for initial literal delimiter: ```
        int startIndex = result.IndexOf(LiteralDelimiter, System.StringComparison.Ordinal);
        if (startIndex < 0)
        {
            // No initial delimiter, return entire expression.
            return result;
        }

        startIndex += LiteralDelimiter.Length;

        // Accommodate "json" prefix, if present.
        if (JsonPrefix.Equals(result.Substring(startIndex, JsonPrefix.Length), System.StringComparison.OrdinalIgnoreCase))
        {
            startIndex += JsonPrefix.Length;
        }

        // Locate final literal delimiter
        int endIndex = result.IndexOf(LiteralDelimiter, startIndex, System.StringComparison.OrdinalIgnoreCase);
        if (endIndex < 0)
        {
            endIndex = result.Length;
        }

        // Extract JSON
        return result.Substring(startIndex, endIndex - startIndex);
    }
}
