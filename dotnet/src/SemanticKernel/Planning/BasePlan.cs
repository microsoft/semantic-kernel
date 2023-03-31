// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

public class BasePlan : IPlan
{
    /// <inheritdoc/>
    [JsonPropertyName("goal")]
    public string Goal { get; set; } = string.Empty;

    /// <inheritdoc/>
    [JsonPropertyName("context_variables")]
    public ContextVariables State { get; set; } = new();

    [JsonPropertyName("steps")]
    private PlanStep _steps { get; set; } = new();

    /// <inheritdoc/>
    public PlanStep Steps => this._steps;

    /// <inheritdoc/>
    public Task<IPlan> RunNextStepAsync(IKernel kernel, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        // no-op, return self
        return Task.FromResult<IPlan>(this);
    }
}
