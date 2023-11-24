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
internal sealed class KernelFunctionFromPrompt : KernelFunction
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
    public static KernelFunction Create(
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
    public static KernelFunction Create(
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
    public static KernelFunction Create(
        IPromptTemplate promptTemplate,
        PromptTemplateConfig promptTemplateConfig,
        string? functionName = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(promptTemplate);
        Verify.NotNull(promptTemplateConfig);

        functionName ??= RandomFunctionName();
        Verify.ValidFunctionName(functionName);

        return new KernelFunctionFromPrompt(
            template: promptTemplate,
            promptTemplateConfig: promptTemplateConfig,
            functionName: functionName,
            loggerFactory: loggerFactory);
    }

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<SKParameterMetadata> Parameters => this._promptTemplate.Parameters;

    /// <inheritdoc/>
    protected override SKFunctionMetadata GetMetadataCore() =>
        this._metadata ??=
        new SKFunctionMetadata(this.Name)
        {
            Description = this._promptTemplateConfig.Description,
            Parameters = this.Parameters
        };

    /// <inheritdoc/>
    protected override async Task<FunctionResult> InvokeCoreAsync(
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

            var invokingEventArgs = this.CallFunctionInvoking(kernel, context, renderedPrompt);
            if (invokingEventArgs.IsSkipRequested || invokingEventArgs.CancelToken.IsCancellationRequested)
            {
                return new FunctionResult(this.Name, context)
                {
                    IsCancellationRequested = invokingEventArgs.CancelToken.IsCancellationRequested,
                    IsSkipRequested = invokingEventArgs.IsSkipRequested
                };
            }

            renderedPrompt = this.GetPromptFromEventArgsMetadataOrDefault(invokingEventArgs, renderedPrompt);

            IReadOnlyList<ITextResult> completionResults = await textCompletion.GetCompletionsAsync(renderedPrompt, requestSettings ?? defaultRequestSettings, cancellationToken).ConfigureAwait(false);
            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            // Update the result with the completion
            context.Variables.Update(completion);

            var modelResults = completionResults.Select(c => c.ModelResult).ToArray();

            var result = new FunctionResult(this.Name, context, completion);

            result.Metadata.Add(AIFunctionResultExtensions.ModelResultsMetadataKey, modelResults);
            result.Metadata.Add(SKEventArgsExtensions.RenderedPromptMetadataKey, renderedPrompt);

            (var invokedEventArgs, result) = this.CallFunctionInvoked(kernel, context, result, renderedPrompt);
            result.IsCancellationRequested = invokedEventArgs.CancelToken.IsCancellationRequested;
            result.IsRepeatRequested = invokedEventArgs.IsRepeatRequested;

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

    private KernelFunctionFromPrompt(
        IPromptTemplate template,
        PromptTemplateConfig promptTemplateConfig,
        string functionName,
        ILoggerFactory? loggerFactory = null) : base(functionName, promptTemplateConfig.Description, promptTemplateConfig.ModelSettings)
    {
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(SKFunctionFactory)) : NullLogger.Instance;

        this._promptTemplate = template;
        this._promptTemplateConfig = promptTemplateConfig;
        Verify.ParametersUniqueness(this.Parameters);
    }

    #region private

    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptTemplateConfig;
    private SKFunctionMetadata? _metadata;
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
    /// <param name="kernel">Kernel instance</param>
    /// <param name="context">Execution context</param>
    /// <param name="renderedPrompt">Rendered prompt</param>
    private FunctionInvokingEventArgs CallFunctionInvoking(Kernel kernel, SKContext context, string renderedPrompt)
    {
        var eventArgs = new FunctionInvokingEventArgs(this.GetMetadata(), context)
        {
            Metadata = {
                [SKEventArgsExtensions.RenderedPromptMetadataKey] = renderedPrompt
            }
        };
        kernel.OnFunctionInvoking(eventArgs);
        return eventArgs;
    }

    /// <summary>
    /// Handles the FunctionInvoked event
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="context">Execution context</param>
    /// <param name="result">Current function result</param>
    /// <param name="prompt">Prompt used by the function</param>
    private (FunctionInvokedEventArgs, FunctionResult) CallFunctionInvoked(Kernel kernel, SKContext context, FunctionResult result, string prompt)
    {
        result.Metadata[SKEventArgsExtensions.RenderedPromptMetadataKey] = prompt;

        var eventArgs = new FunctionInvokedEventArgs(this.GetMetadata(), result);
        if (kernel.OnFunctionInvoked(eventArgs))
        {
            // Apply any changes from the event handlers to final result.
            result = new FunctionResult(this.Name, eventArgs.SKContext, eventArgs.SKContext.Variables.Input)
            {
                // Updates the eventArgs metadata during invoked handler execution
                // will reflect in the result metadata
                Metadata = eventArgs.Metadata
            };
        }

        return (eventArgs, result);
    }

    /// <summary>
    /// Try to get the prompt from the event args metadata.
    /// </summary>
    /// <param name="eventArgs">Function invoking event args</param>
    /// <param name="defaultPrompt">Default prompt if none is found in metadata</param>
    /// <returns></returns>
    private string GetPromptFromEventArgsMetadataOrDefault(FunctionInvokingEventArgs eventArgs, string defaultPrompt)
    {
        if (!eventArgs.Metadata.TryGetValue(SKEventArgsExtensions.RenderedPromptMetadataKey, out var renderedPromptFromMetadata))
        {
            return defaultPrompt;
        }

        // If prompt key exists and was modified to null default to an empty string
        return renderedPromptFromMetadata?.ToString() ?? string.Empty;
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";
    #endregion
}
