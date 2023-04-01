// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Base implementation of a plan
/// </summary>
public class BasePlan : IPlan
{
    /// <inheritdoc/>
    [JsonPropertyName("state")]
    public ContextVariables State { get; set; } = new();

    /// <inheritdoc/>
    [JsonPropertyName("root")]
    public PlanStep Root { get; set; } = new();

    /// <inheritdoc/>
    public Task<IPlan> RunNextStepAsync(IKernel kernel, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        // no-op, return self
        return Task.FromResult<IPlan>(this);
    }
}
