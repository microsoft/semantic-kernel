// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;
internal abstract class FunctionBase : ISKFunction
{
    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string SkillName { get; }

    /// <inheritdoc/>
    public string Description { get; }

    /// <inheritdoc/>
    public abstract bool IsSemantic { get; }

    /// <inheritdoc/>
    public CompleteRequestSettings RequestSettings { get; protected set; } = new();

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IList<ParameterView> Parameters { get; }

    internal FunctionBase(
        string functionName,
        string skillName,
        string description,
        IList<ParameterView> parameters,
        ILogger logger)
    {
        Verify.ValidSkillName(skillName);
        Verify.ValidFunctionName(functionName);
        Verify.ParametersUniqueness(parameters);

        this.Name = functionName;
        this.SkillName = skillName;
        this.Description = description;
        this.Parameters = parameters;
        this._logger = logger;
    }

    /// <inheritdoc/>
    public FunctionView Describe()
    {
        return new FunctionView
        {
            IsSemantic = this.IsSemantic,
            Name = this.Name,
            SkillName = this.SkillName,
            Description = this.Description,
            Parameters = this.Parameters,
        };
    }

    /// <summary>
    /// JSON serialized string representation of the function.
    /// </summary>
    public override string ToString()
        => this.ToString(false);

    /// <summary>
    /// JSON serialized string representation of the function.
    /// </summary>
    public string ToString(bool writeIndented)
        => JsonSerializer.Serialize(this, options: writeIndented ? s_toStringIndentedSerialization : s_toStringStandardSerialization);

    /// <inheritdoc/>
    public virtual Task<FunctionInvokingEventArgs> PrepareFunctionInvokingEventArgsAsync(SKContext context)
    {
        return Task.FromResult(new FunctionInvokingEventArgs(this.Describe(), context));
    }

    /// <inheritdoc/>
    public virtual Task<FunctionInvokedEventArgs> PrepareFunctionInvokedEventArgsAsync(SKContext context)
    {
        return Task.FromResult(new FunctionInvokedEventArgs(this.Describe(), context));
    }

    /// <inheritdoc/>
    public abstract Task<SKContext> InvokeAsync(SKContext context, CompleteRequestSettings? settings = null, CancellationToken cancellationToken = default);

    /// <inheritdoc/>
    public abstract ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills);

    /// <inheritdoc/>
    public abstract ISKFunction SetAIService(Func<ITextCompletion> serviceFactory);

    /// <inheritdoc/>
    public abstract ISKFunction SetAIConfiguration(CompleteRequestSettings settings);

    protected readonly ILogger _logger;

    private static readonly JsonSerializerOptions s_toStringStandardSerialization = new();
    private static readonly JsonSerializerOptions s_toStringIndentedSerialization = new() { WriteIndented = true };
}
