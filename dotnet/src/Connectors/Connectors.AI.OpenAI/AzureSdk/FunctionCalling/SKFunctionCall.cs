// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk.FunctionCalling;

using System;
using System.Threading;
using System.Threading.Tasks;
using Orchestration;
using SemanticKernel.AI.TextCompletion;
using SkillDefinition;


public class SKFunctionCall : ISKFunction
{

    /// <inheritdoc />
    public string Name { get; }

    /// <inheritdoc />
    public string SkillName { get; }

    /// <inheritdoc />
    public string Description { get; }

    /// <inheritdoc />
    public bool IsSemantic { get; }

    /// <inheritdoc />
    public CompleteRequestSettings RequestSettings { get; }


    /// <inheritdoc />
    public FunctionView Describe() => null;


    /// <inheritdoc />
    public async Task<SKContext> InvokeAsync(SKContext context, CompleteRequestSettings? settings = null, CancellationToken cancellationToken = default) => null;


    /// <inheritdoc />
    public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills) => null;


    /// <inheritdoc />
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory) => null;


    /// <inheritdoc />
    public ISKFunction SetAIConfiguration(CompleteRequestSettings settings) => null;
}
