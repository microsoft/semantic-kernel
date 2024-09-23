// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Security;

namespace Microsoft.SemanticKernel.SkillDefinition;

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
    bool IsSemantic { get; }

    /// <summary>
    /// Whether the function is set to be sensitive (default false).
    /// When a function is sensitive, the default trust service will throw an exception
    /// if the function is invoked passing in some untrusted input (or context, or prompt).
    /// </summary>
    bool IsSensitive { get; }

    /// <summary>
    /// Service used for trust check events.
    /// This can be provided at function creation, if not, the TrustService.DefaultTrusted implementation will be used.
    /// </summary>
    ITrustService TrustServiceInstance { get; }

    /// <summary>
    /// AI service settings
    /// </summary>
    JsonObject ServiceSettings { get; }

    /// <summary>
    /// Returns a description of the function, including parameters.
    /// </summary>
    /// <returns>An instance of <see cref="FunctionView"/> describing the function</returns>
    FunctionView Describe();

    /// <summary>
    /// Invoke the <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="context">SK context</param>
    /// <param name="textCompletionService">Text completion service.</param>
    /// <param name="settings">LLM completion settings (for semantic functions only)</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    Task<SKContext> InvokeAsync(
        SKContext context,
        ITextCompletion? textCompletionService = null,
        CompleteRequestSettings? settings = null);
        string input,
        SKContext? context = null,
        JsonObject? settings = null,
        ILogger? log = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Invoke the <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="input">String input</param>
    /// <param name="textCompletionService">Text completion service.</param>
    /// <param name="settings">LLM completion settings (for semantic functions only)</param>
    /// <param name="skills">Available skills.</param>
    /// <param name="memory">Semantic memory</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    Task<SKContext> InvokeAsync(
        string? input = null,
        ITextCompletion? textCompletionService = null,
        CompleteRequestSettings? settings = null,
        IReadOnlySkillCollection? skills = null,
        ISemanticTextMemory? memory = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Set the AI completion settings used with LLM requests
        SKContext? context = null,
        JsonObject? settings = null,
        ILogger? log = null,
        CancellationToken cancellationToken = default);

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
    /// Set the AI settings used with LLM requests
    /// </summary>
    /// <param name="settings">LLM settings</param>
    /// <returns>Self instance</returns>
    ISKFunction SetAIConfiguration(JsonObject settings);
}
