// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Generic Token counts record for exposing the token usage.
/// </summary>
/// <param name="CompletionTokens"></param>
/// <param name="PromptTokens"></param>
/// <param name="TotalTokens"></param>
public sealed record TokenCounts(int CompletionTokens, int PromptTokens, int TotalTokens);

/// <summary>
/// Kernel result Strongly Typed Wrapper after execution.
/// </summary>
public record KernelResultExtended
{
    /// <summary>
    /// Represents the result of the kernel execution.
    /// </summary>
    public string Result { get; init; }
    /// <summary>
    /// Represent the usage in Tokens.
    /// </summary>
    public TokenCounts? TokenCounts { get; set; }

    /// <summary>
    /// Kernel result after execution.
    /// </summary>
    public KernelResult KernelResult { get; init; }

    /// <summary>
    /// Represents a result from a model execution.
    /// </summary>
    public IEnumerable<ModelResult> ModelResult { get; init; }

    /// <summary>
    /// Creates the strongyl typed wrapper from the KernelResult.
    /// </summary>
    /// <param name="kernelResult"></param>
    public KernelResultExtended(KernelResult kernelResult)
    {
        this.KernelResult = kernelResult;
        this.Result = this.ParseResultFromKernelResult();
        this.ModelResult = this.ParseModelResult();
    }

    private string ParseResultFromKernelResult()
    {
        return this.KernelResult.GetValue<string>() ?? string.Empty;
    }

    private IEnumerable<ModelResult> ParseModelResult()
    {
        return this.KernelResult.FunctionResults.SelectMany(
            l => l.GetModelResults() ?? Enumerable.Empty<ModelResult>());
    }
}
