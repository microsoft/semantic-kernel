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
        if (result.Metadata.TryGetValue(ModelResultsMetadataKey, out object modelResultObject) &&
            modelResultObject is IReadOnlyCollection<ModelResult> modelResults)
        {
            return modelResults;
        }

        return null;
    }
}
