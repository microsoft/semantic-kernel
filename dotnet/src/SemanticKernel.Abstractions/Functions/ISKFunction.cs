// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Semantic Kernel callable function interface
/// </summary>
public interface ISKFunction
{
    /// <summary>
    /// Name of the function. The name is used by the function collection and in prompt templates e.g. {{pluginName.functionName}}
    /// </summary>
    string Name { get; }

    /// <summary>
    /// Name of the plugin containing the function. The name is used by the function collection and in prompt templates e.g. {{pluginName.functionName}}
    /// </summary>
    string PluginName { get; }

    /// <summary>
    /// Function description. The description is used in combination with embeddings when searching relevant functions.
    /// </summary>
    string Description { get; }

    /// <summary>
    /// Returns a description of the function, including parameters.
    /// </summary>
    /// <returns>An instance of <see cref="FunctionView"/> describing the function</returns>
    FunctionView Describe();

    /// <summary>
    /// Invoke the <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="context">SK context</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<FunctionResult> InvokeAsync(
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);

    #region Obsolete

    /// <summary>
    /// AI service settings
    /// </summary>
    [Obsolete("Use PromptTemplateConfig.ModelSettings instead. This will be removed in a future release.")]
    AIRequestSettings? RequestSettings { get; }

    /// <summary>
    /// Set the AI service used by the semantic function, passing a factory method.
    /// The factory allows to lazily instantiate the client and to properly handle its disposal.
    /// </summary>
    /// <param name="serviceFactory">AI service factory</param>
    /// <returns>Self instance</returns>
    [Obsolete("Use implementation of IAIServiceConfigurationProvider instead. This will be removed in a future release.")]
    ISKFunction SetAIService(Func<ITextCompletion> serviceFactory);

    /// <summary>
    /// Set the AI completion settings used with LLM requests
    /// </summary>
    /// <param name="requestSettings">LLM completion settings</param>
    /// <returns>Self instance</returns>
    [Obsolete("Use implementation of IAIServiceConfigurationProvider instead. This will be removed in a future release.")]
    ISKFunction SetAIConfiguration(AIRequestSettings? requestSettings);

    /// <summary>
    /// Name of the plugin containing the function. The name is used by the function collection and in prompt templates e.g. {{skillName.functionName}}
    /// </summary>
    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.SkillName instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    string SkillName { get; }

    /// <summary>
    /// Set the default function collection to use when the function is invoked
    /// without a context or with a context that doesn't have a collection.
    /// </summary>
    /// <param name="skills">Kernel's function collection</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is a nop and will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    ISKFunction SetDefaultSkillCollection(IReadOnlyFunctionCollection skills);

    /// <summary>
    /// Set the default function collection to use when the function is invoked
    /// without a context or with a context that doesn't have a collection.
    /// </summary>
    /// <param name="functions">Kernel's function collection</param>
    /// <returns>Self instance</returns>
    [Obsolete("This method is a nop and will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    ISKFunction SetDefaultFunctionCollection(IReadOnlyFunctionCollection functions);

    /// <summary>
    /// Whether the function is defined using a prompt template.
    /// IMPORTANT: native functions might use semantic functions internally,
    /// so when this property is False, executing the function might still involve AI calls.
    /// </summary>
    [Obsolete("Kernel no longer differentiates between Semantic and Native functions. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    bool IsSemantic { get; }

    #endregion
}
