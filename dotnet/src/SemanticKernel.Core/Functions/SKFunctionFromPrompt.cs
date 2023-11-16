// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;

#pragma warning disable IDE0130

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides factory methods for creating <see cref="ISKFunction"/> instances backed by a prompt to be submitted to an LLM.
/// </summary>
public static class KernelFunctionFromPrompt
{
    // TODO: Revise these Create method XML comments

    /// <summary>
    /// Creates a string-to-string semantic function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="requestSettings">Optional LLM request settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction Create(
        string promptTemplate,
        AIRequestSettings? requestSettings = null,
        string? functionName = null,
        string? description = null,
        ILoggerFactory? loggerFactory = null)
    {
        functionName ??= RandomFunctionName();

        var promptTemplateConfig = new PromptTemplateConfig
        {
            Description = description ?? "Generic function, unknown purpose",
        };

        if (requestSettings is not null)
        {
            promptTemplateConfig.ModelSettings.Add(requestSettings);
        }

        return Create(
            promptTemplate: promptTemplate,
            promptTemplateConfig: promptTemplateConfig,
            functionName: functionName,
            loggerFactory: loggerFactory);
    }

    /// <summary>
    /// Creates a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction Create(
        string promptTemplate,
        PromptTemplateConfig promptTemplateConfig,
        string? functionName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var factory = promptTemplateFactory ?? CreateDefaultPromptTemplateFactory(loggerFactory);

        return Create(
            factory.Create(promptTemplate, promptTemplateConfig),
            promptTemplateConfig,
            functionName,
            loggerFactory);
    }

    /// <summary>
    /// Allow to define a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction Create(
        IPromptTemplate promptTemplate,
        PromptTemplateConfig promptTemplateConfig,
        string? functionName = null,
        ILoggerFactory? loggerFactory = null)
    {
        functionName ??= RandomFunctionName();
        Verify.ValidFunctionName(functionName);

        return SemanticFunction.FromSemanticConfig(
            functionName, promptTemplateConfig,
            promptTemplate,
            loggerFactory);
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";

    /// <summary>
    /// Create a default prompt template factory.
    ///
    /// TODO:
    /// This is a temporary solution to avoid breaking existing clients.
    /// There will be a separate task to add support for registering instances of IPromptTemplateEngine and obsoleting the current approach.
    /// </summary>
    internal static IPromptTemplateFactory CreateDefaultPromptTemplateFactory(ILoggerFactory? loggerFactory)
    {
        return
            (IPromptTemplateFactory?)s_promptTemplateFactoryType?.Value?.Invoke(new object?[] { loggerFactory }) ??
            new NullPromptTemplateFactory();
    }

    private const string BasicTemplateFactoryAssemblyName = "Microsoft.SemanticKernel.TemplateEngine.Basic";

    private static readonly Lazy<ConstructorInfo?> s_promptTemplateFactoryType = new(() =>
    {
        try
        {
            const string BasicTemplateFactoryTypeName = "BasicPromptTemplateFactory";

            var assembly = Assembly.Load(BasicTemplateFactoryAssemblyName);

            return assembly.ExportedTypes.SingleOrDefault(type =>
                type.Name.Equals(BasicTemplateFactoryTypeName, StringComparison.Ordinal) &&
                type.GetInterface(nameof(IPromptTemplateFactory)) is not null)?.GetConstructor(new Type[] { typeof(ILoggerFactory) });
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            return null;
        }
    });

    /// <summary>
    /// Default implementation to identify if a function was cancelled or skipped.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingCancelOrSkipRequested(SKContext context) =>
        IsInvokingCancelRequested(context) || IsInvokingSkipRequested(context);

    /// <summary>
    /// Default implementation to identify if a function was skipped.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingSkipRequested(SKContext context) =>
        context.FunctionInvokingHandler?.EventArgs?.IsSkipRequested == true;

    /// <summary>
    /// Default implementation to identify if a function was cancelled in the pre hook.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingCancelRequested(SKContext context) =>
        context.FunctionInvokingHandler?.EventArgs?.CancelToken.IsCancellationRequested == true;

    /// <summary>
    /// Default implementation to identify if a function was cancelled in the post hook.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokedCancelRequested(SKContext context) =>
        context.FunctionInvokedHandler?.EventArgs?.CancelToken.IsCancellationRequested == true;

    private sealed class NullPromptTemplateFactory : IPromptTemplateFactory
    {
        public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig) =>
            new NullPromptTemplate(templateString);
    }

    private sealed class NullPromptTemplate : IPromptTemplate
    {
        private readonly string _templateText;

        public NullPromptTemplate(string templateText) => this._templateText = templateText;

        public IReadOnlyList<ParameterView> Parameters => Array.Empty<ParameterView>();

        public Task<string> RenderAsync(Kernel kernel, SKContext executionContext, CancellationToken cancellationToken = default) =>
            Task.FromResult(this._templateText);
    }
}
