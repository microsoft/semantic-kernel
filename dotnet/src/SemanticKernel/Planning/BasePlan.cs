// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Base implementation of a plan
/// </summary>
public class BasePlan : Plan
{
    /// <inheritdoc/>
    public override FunctionView Describe()
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public override Task<SKContext> InvokeAsync(string input, SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null, CancellationToken? cancel = null)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public override Task<SKContext> InvokeAsync(SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null, CancellationToken? cancel = null)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public override Task<Plan> RunNextStepAsync(IKernel kernel, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        // no-op, return self
        return Task.FromResult<Plan>(this);
    }

    /// <inheritdoc/>
    public override ISKFunction SetAIConfiguration(CompleteRequestSettings settings)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public override ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public override ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills)
    {
        throw new NotImplementedException();
    }
}
