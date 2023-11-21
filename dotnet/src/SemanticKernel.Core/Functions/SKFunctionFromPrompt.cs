// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// A Semantic Kernel "Semantic" prompt function.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class SKFunctionFromPrompt : ISKFunction
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
        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(loggerFactory);

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
        Verify.NotNull(promptTemplate);
        Verify.NotNull(promptTemplateConfig);

        functionName ??= RandomFunctionName();
        Verify.ValidFunctionName(functionName);

        return new SKFunctionFromPrompt(
            template: promptTemplate,
            promptTemplateConfig: promptTemplateConfig,
            functionName: functionName,
            loggerFactory: loggerFactory);
    }

    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string Description => this._promptTemplateConfig.Description;

    /// <inheritdoc/>
    public IEnumerable<AIRequestSettings> ModelSettings => this._promptTemplateConfig.ModelSettings.AsReadOnly();

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<SKParameterMetadata> Parameters => this._promptTemplate.Parameters;

    /// <inheritdoc/>
    public SKFunctionMetadata GetMetadata() =>
        this._view ??=
        new SKFunctionMetadata(this.Name)
        {
            Description = this._promptTemplateConfig.Description,
            Parameters = this.Parameters
        };

    /// <inheritdoc/>
    public async Task<FunctionResult> InvokeAsync(
        Kernel kernel,
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(context.Variables);

        try
        {
            string renderedPrompt = await this._promptTemplate.RenderAsync(kernel, context, cancellationToken).ConfigureAwait(false);

            var serviceSelector = kernel.ServiceSelector;
            (var textCompletion, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, context, this);
            Verify.NotNull(textCompletion);

            this.CallFunctionInvoking(context, renderedPrompt);
            if (IsInvokingCancelOrSkipRequested(context))
            {
                return new FunctionResult(this.Name, context);
            }

            renderedPrompt = this.GetPromptFromEventArgsMetadataOrDefault(context, renderedPrompt);

            IReadOnlyList<ITextResult> completionResults = await textCompletion.GetCompletionsAsync(renderedPrompt, requestSettings ?? defaultRequestSettings, cancellationToken).ConfigureAwait(false);
            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            // Update the result with the completion
            context.Variables.Update(completion);

            var modelResults = completionResults.Select(c => c.ModelResult).ToArray();

            var result = new FunctionResult(this.Name, context, completion);

            result.Metadata.Add(AIFunctionResultExtensions.ModelResultsMetadataKey, modelResults);
            result.Metadata.Add(SKEventArgsExtensions.RenderedPromptMetadataKey, renderedPrompt);

            this.CallFunctionInvoked(result, context, renderedPrompt);
            if (IsInvokedCancelRequested(context))
            {
                result = new FunctionResult(this.Name, context, result.Value);
            }

            return result;
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            this._logger?.LogError(ex, "Semantic function {Name} execution failed with error {Error}", this.Name, ex.Message);
            throw;
        }
    }

    /// <summary>
    /// JSON serialized string representation of the function.
    /// </summary>
    public override string ToString() => JsonSerializer.Serialize(this);

    private SKFunctionFromPrompt(
        IPromptTemplate template,
        PromptTemplateConfig promptTemplateConfig,
        string functionName,
        ILoggerFactory? loggerFactory = null)
    {
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(SKFunction)) : NullLogger.Instance;

        this._promptTemplate = template;
        this._promptTemplateConfig = promptTemplateConfig;
        Verify.ParametersUniqueness(this.Parameters);

        this.Name = functionName;
    }

    #region private

    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptTemplateConfig;
    private SKFunctionMetadata? _view;
    private readonly IPromptTemplate _promptTemplate;

    private static async Task<string> GetCompletionsResultContentAsync(IReadOnlyList<ITextResult> completions, CancellationToken cancellationToken = default)
    {
        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        return await completions[0].GetCompletionAsync(cancellationToken).ConfigureAwait(false);
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrWhiteSpace(this.Description) ? this.Name : $"{this.Name} ({this.Description})";

    /// <summary>Add default values to the context variables if the variable is not defined</summary>
    private void AddDefaultValues(ContextVariables variables)
    {
        foreach (var parameter in this.Parameters)
        {
            if (!variables.ContainsKey(parameter.Name) && parameter.DefaultValue != null)
            {
                variables[parameter.Name] = parameter.DefaultValue;
            }
        }
    }

    /// <summary>
    /// Handles the FunctionInvoking event
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <param name="renderedPrompt">Rendered prompt</param>
    private void CallFunctionInvoking(SKContext context, string renderedPrompt)
    {
        var eventWrapper = context.FunctionInvokingHandler;
        if (eventWrapper?.Handler is null)
        {
            return;
        }

        eventWrapper.EventArgs = new FunctionInvokingEventArgs(this.GetMetadata(), context)
        {
            Metadata = {
                [SKEventArgsExtensions.RenderedPromptMetadataKey] = renderedPrompt
            }
        };
        eventWrapper.Handler.Invoke(this, eventWrapper.EventArgs);
    }

    /// <summary>
    /// Handles the FunctionInvoked event
    /// </summary>
    /// <param name="result">Current function result</param>
    /// <param name="context">Execution context</param>
    /// <param name="prompt">Prompt used by the function</param>
    private void CallFunctionInvoked(FunctionResult result, SKContext context, string prompt)
    {
        var eventWrapper = context.FunctionInvokedHandler;

        result.Metadata[SKEventArgsExtensions.RenderedPromptMetadataKey] = prompt;

        // Not handlers registered, return the result as is
        if (eventWrapper?.Handler is null)
        {
            return;
        }

        eventWrapper.EventArgs = new FunctionInvokedEventArgs(this.GetMetadata(), result);
        eventWrapper.Handler.Invoke(this, eventWrapper.EventArgs);

        // Updates the eventArgs metadata during invoked handler execution
        // will reflect in the result metadata
        result.Metadata = eventWrapper.EventArgs.Metadata;
    }

    /// <summary>
    /// Try to get the prompt from the event args metadata.
    /// </summary>
    /// <param name="context"></param>
    /// <param name="defaultPrompt">Default prompt if none is found in metadata</param>
    /// <returns></returns>
    private string GetPromptFromEventArgsMetadataOrDefault(SKContext context, string defaultPrompt)
    {
        var eventArgs = context.FunctionInvokingHandler?.EventArgs;
        if (eventArgs is null || !eventArgs.Metadata.TryGetValue(SKEventArgsExtensions.RenderedPromptMetadataKey, out var renderedPromptFromMetadata))
        {
            return defaultPrompt;
        }

        // If prompt key exists and was modified to null default to an empty string
        return renderedPromptFromMetadata?.ToString() ?? string.Empty;
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";

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

        private sealed class NullPromptTemplate : IPromptTemplate
        {
            private readonly string _templateText;

            public NullPromptTemplate(string templateText) => this._templateText = templateText;

            public IReadOnlyList<SKParameterMetadata> Parameters => Array.Empty<SKParameterMetadata>();

            public Task<string> RenderAsync(Kernel kernel, SKContext executionContext, CancellationToken cancellationToken = default) =>
                Task.FromResult(this._templateText);
        }
    }

    #endregion
}
