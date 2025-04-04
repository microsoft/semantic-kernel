// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

internal sealed class QualifiedResult
{
    public string? Answer { get; init; }

    public decimal Confidence { get; init; }
}

internal sealed class TriageResult
{
    public QualifiedResult? Analyze { get; init; }

    public QualifiedResult? Query { get; init; }

    public bool TryGetAnalyzeResult(decimal confidenceThreshold, [NotNullWhen(true)] out string? response)
        => this.TryGetResult(this.Analyze, confidenceThreshold, out response);

    public bool TryGetQueryResult(decimal confidenceThreshold, [NotNullWhen(true)] out string? response)
        => this.TryGetResult(this.Query, confidenceThreshold, out response);

    public bool TryGetResult(QualifiedResult? result, decimal confidenceThreshold, [NotNullWhen(true)] out string? response)
    {
        if (string.IsNullOrEmpty(result?.Answer))
        {
            response = null;
            return false;
        }

        response = result.Answer;
        return result.Confidence >= confidenceThreshold;
    }
}
