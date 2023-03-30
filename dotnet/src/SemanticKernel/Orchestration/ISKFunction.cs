// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Semantic Kernel callable function interface
/// </summary>
public interface ISKFunction
{
    /// <summary>
    /// Name of the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    /// </summary>
    string Name { get; }

    /// <summary>
    /// Name of the skill containing the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
    /// </summary>
    string SkillName { get; }

    /// <summary>
    /// Function description. The description is used in combination with embeddings when searching relevant functions.
    /// </summary>
    string Description { get; }

    /// <summary>
    /// Whether the function is defined using a prompt template.
    /// IMPORTANT: native functions might use semantic functions internally,
    /// so when this property is False, executing the function might still involve AI calls.
    /// </summary>
    public bool IsSemantic { get; }

    /// <summary>
    /// AI service settings
    /// </summary>
    public CompleteRequestSettings RequestSettings { get; }

    /// <summary>
    /// Returns a description of the function, including parameters.
    /// </summary>
    /// <returns>An instance of <see cref="FunctionView"/> describing the function</returns>
    FunctionView Describe();

    /// <summary>
    /// Invoke the internal delegate with an explicit string input
    /// </summary>
    /// <param name="input">String input</param>
    /// <param name="context">SK context</param>
    /// <param name="settings">LLM completion settings</param>
    /// <param name="log">Application logger</param>
    /// <param name="cancel">Cancellation token</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    Task<SKContext> InvokeAsync(
        string input,
        SKContext? context = null,
        CompleteRequestSettings? settings = null,
        ILogger? log = null,
        CancellationToken? cancel = null);

    /// <summary>
    /// Invoke the internal delegate
    /// </summary>
    /// <param name="context">SK context</param>
    /// <param name="settings">LLM completion settings</param>
    /// <param name="log">Application logger</param>
    /// <param name="cancel">Cancellation token</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    Task<SKContext> InvokeAsync(
        SKContext? context = null,
        CompleteRequestSettings? settings = null,
        ILogger? log = null,
        CancellationToken? cancel = null);

    /// <summary>
    /// Set the default skill collection to use when the function is invoked
    /// without a context or with a context that doesn't have a collection.
    /// </summary>
    /// <param name="skills">Kernel's skill collection</param>
    /// <returns>Self instance</returns>
    ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills);

    /// <summary>
    /// Set the AI service used by the semantic function, passing a factory method.
    /// The factory allows to lazily instantiate the client and to properly handle its disposal.
    /// </summary>
    /// <param name="serviceFactory">AI service factory</param>
    /// <returns>Self instance</returns>
    ISKFunction SetAIService(Func<ITextCompletion> serviceFactory);

    /// <summary>
    /// Set the AI completion settings used with LLM requests
    /// </summary>
    /// <param name="settings">LLM completion settings</param>
    /// <returns>Self instance</returns>
    ISKFunction SetAIConfiguration(CompleteRequestSettings settings);
}
