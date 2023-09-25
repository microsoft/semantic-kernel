// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Class with extension methods related to AI logic for <see cref="FunctionResult"/> class.
/// </summary>
public static class AIFunctionResultExtensions
{
    /// <summary>
    /// Function result metadata key for <see cref="ModelResult"/> records.
    /// </summary>
    public const string ModelResultsMetadataKey = "ModelResults";

    /// <summary>
    /// Returns collection of <see cref="ModelResult"/> records from <see cref="FunctionResult"/> metadata.
    /// </summary>
    /// <param name="result">Instance of <see cref="FunctionResult"/> class.</param>
    public static IReadOnlyCollection<ModelResult>? GetModelResults(this FunctionResult result)
    {
        if (result.TryGetValue(ModelResultsMetadataKey, out IReadOnlyCollection<ModelResult>? modelResults))
        {
            return modelResults;
        }

        return null;
    }

    /// <summary>
    /// Get typed value from <see cref="FunctionResult"/> metadata.
    /// </summary>
    public static bool TryGetValue<T>(this FunctionResult result, string key, out T value)
    {
        if (result.Metadata.TryGetValue(key, out object? valueObject) &&
            valueObject is T valueT)
        {
            value = valueT;
            return true;
        }

        value = default!;
        return false;
    }

    /// <summary>
    /// Adds collection of <see cref="ModelResult"/> records to <see cref="FunctionResult"/> metadata.
    /// </summary>
    /// <param name="result">Instance of <see cref="FunctionResult"/> class.</param>
    /// <param name="modelResults">Collection of <see cref="ModelResult"/> records.</param>
    internal static void AddModelResults(this FunctionResult result, IReadOnlyCollection<ModelResult> modelResults)
    {
        result.Metadata.Add(ModelResultsMetadataKey, modelResults);
    }
}
