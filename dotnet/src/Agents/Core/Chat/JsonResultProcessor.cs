// Copyright (c) Microsoft. All rights reserved.
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
public sealed class JsonResultProcessor<TResult>() : FunctionResultProcessor<TResult>()
{
    /// <inheritdoc/>
    protected override TResult? ProcessTextResult(string result)
        => JsonResultTranslator.Translate<TResult>(result);
}
