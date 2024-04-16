// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;

namespace Microsoft.SemanticKernel.Agents.Chat;
/// <summary>
/// Supports parsing json from a <see cref="FunctionResult"/>.  Includes delimiter trimming
/// of literals:
/// <example>
/// [json]
/// </example>
/// <example>
/// ```
/// [json]
/// ```
/// </example>
/// <example>
/// ```json
/// [json]
/// ```
/// </example>
/// </summary>
/// <typeparam name="TResult">The target type of the <see cref="FunctionResult"/>.</typeparam>
public sealed class JsonResultParser<TResult>() : FunctionResultProcessor<TResult>()
{
    private const string LiteralDelimeter = "```";
    private const string JsonPrefix = "json";

    /// <inheritdoc/>
    protected override TResult? ProcessTextResult(string result)
    {
        string rawJson = ExtractJson(result);

        return JsonSerializer.Deserialize<TResult>(rawJson);
    }

    private static string ExtractJson(string result)
    {
        // Search for initial literal delimiter: ```
        int startIndex = result.IndexOf(LiteralDelimeter, System.StringComparison.Ordinal);
        if (startIndex < 0)
        {
            // No initial delimiter, return entire expression.
            return result;
        }

        // Accomodate "json" prefix, if present.
        if (JsonPrefix.Equals(result.Substring(startIndex, JsonPrefix.Length), System.StringComparison.OrdinalIgnoreCase))
        {
            startIndex += JsonPrefix.Length;
        }

        // Locate final literal delimiter
        int endIndex = result.IndexOf(LiteralDelimeter, startIndex, System.StringComparison.OrdinalIgnoreCase);
        if (endIndex < 0)
        {
            endIndex = result.Length - 1;
        }

        // Extract JSON
        return result.Substring(startIndex, endIndex - startIndex);
    }
}
