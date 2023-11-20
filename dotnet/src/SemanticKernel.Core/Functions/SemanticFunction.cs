// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Functions;
using Microsoft.SemanticKernel.Models;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

#pragma warning disable format

/// <summary>
/// A Semantic Kernel "Semantic" prompt function.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class SemanticFunction : ISKFunction, IDisposable
{
    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string PluginName { get; }

    /// <inheritdoc/>
    public string Description => this._promptTemplateConfig.Description;

    /// <inheritdoc/>
    public IEnumerable<AIRequestSettings> ModelSettings => this._promptTemplateConfig.ModelSettings.AsReadOnly();

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters => this._promptTemplate.Parameters;

    /// <inheritdoc/>
    public FunctionView Describe()
    {
        return new FunctionView(this.Name, this.PluginName, this.Description) { Parameters = this.Parameters };
    }

    /// <inheritdoc/>
    public async Task<FunctionResult> InvokeAsync(
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(context.Variables);

        return await this.RunPromptAsync(requestSettings, context, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
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

    internal SemanticFunction(
        IPromptTemplate template,
        PromptTemplateConfig promptTemplateConfig,
        string pluginName,
        string functionName,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(template);
        Verify.ValidPluginName(pluginName);
        Verify.ValidFunctionName(functionName);

        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(SemanticFunction)) : NullLogger.Instance;

        this._promptTemplate = template;
        this._promptTemplateConfig = promptTemplateConfig;
        Verify.ParametersUniqueness(this.Parameters);

        this.Name = functionName;
        this.PluginName = pluginName;

        this._view = new(() => new(functionName, pluginName, promptTemplateConfig.Description, this.Parameters));
    }

    /// <summary>
    /// Create a semantic function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="pluginName">Name of the plugin to which the function being created belongs.</param>
    /// <param name="functionName">Name of the function to create.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="promptTemplate">Prompt template.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>SK function instance.</returns>
    public static ISKFunction FromSemanticConfig(
        string pluginName,
        string functionName,
        PromptTemplateConfig promptTemplateConfig,
        IPromptTemplate promptTemplate,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(promptTemplateConfig);
        Verify.NotNull(promptTemplate);

        return new SemanticFunction(
            template: promptTemplate,
            promptTemplateConfig: promptTemplateConfig,
            pluginName: pluginName,
            functionName: functionName,
            loggerFactory: loggerFactory
        );
    }

    /// <summary>
    /// Create a semantic function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="promptFunctionModel"></param>
    /// <param name="pluginName">Name of the plugin to which the function being created belongs.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/> wrapper for <paramref name="promptFunctionModel"/>.</returns>
    public static ISKFunction Create(
        PromptFunctionModel promptFunctionModel,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory ? loggerFactory = null)
    {
        Verify.NotNull(promptFunctionModel);
        Verify.NotNull(promptFunctionModel.Name);
        Verify.NotNull(promptFunctionModel.Template);

        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory();
        var promptTemplateConfig = PromptTemplateConfig.ToPromptTemplateConfig(promptFunctionModel);
        var promptTemplate = factory.Create(promptFunctionModel.Template, promptTemplateConfig);

        return new SemanticFunction(
            template: promptTemplate,
            promptTemplateConfig: promptTemplateConfig,
            pluginName: pluginName ??= FunctionCollection.GlobalFunctionsPluginName,
            functionName: promptFunctionModel.Name,
            loggerFactory: loggerFactory
        );
    }

    #region private

    private static readonly JsonSerializerOptions s_toStringStandardSerialization = new();
    private static readonly JsonSerializerOptions s_toStringIndentedSerialization = new() { WriteIndented = true };
    private readonly ILogger _logger;
    private IAIServiceSelector? _serviceSelector;
    private readonly PromptTemplateConfig _promptTemplateConfig;
    private readonly Lazy<FunctionView> _view;
    private readonly IPromptTemplate _promptTemplate;

    private static async Task<string> GetCompletionsResultContentAsync(IReadOnlyList<ITextResult> completions, CancellationToken cancellationToken = default)
    {
        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        return await completions[0].GetCompletionAsync(cancellationToken).ConfigureAwait(false);
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"{this.Name} ({this.Description})";

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

    private async Task<FunctionResult> RunPromptAsync(
        AIRequestSettings? requestSettings,
        SKContext context,
        CancellationToken cancellationToken = default)
    {
        FunctionResult result;

        try
        {
            string renderedPrompt = await this._promptTemplate.RenderAsync(context, cancellationToken).ConfigureAwait(false);

            var serviceSelector = this._serviceSelector ?? context.ServiceSelector;
            (var textCompletion, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(context, this);
            Verify.NotNull(textCompletion);

            this.CallFunctionInvoking(context, renderedPrompt);
            if (SKFunction.IsInvokingCancelOrSkipRequested(context))
            {
                return new FunctionResult(this.Name, this.PluginName, context);
            }

            renderedPrompt = this.GetPromptFromEventArgsMetadataOrDefault(context, renderedPrompt);

            IReadOnlyList<ITextResult> completionResults = await textCompletion.GetCompletionsAsync(renderedPrompt, requestSettings ?? defaultRequestSettings, cancellationToken).ConfigureAwait(false);
            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            // Update the result with the completion
            context.Variables.Update(completion);

            var modelResults = completionResults.Select(c => c.ModelResult).ToArray();

            result = new FunctionResult(this.Name, this.PluginName, context, completion);

            result.Metadata.Add(AIFunctionResultExtensions.ModelResultsMetadataKey, modelResults);
            result.Metadata.Add(SKEventArgsExtensions.RenderedPromptMetadataKey, renderedPrompt);

            this.CallFunctionInvoked(result, context, renderedPrompt);
            if (SKFunction.IsInvokedCancelRequested(context))
            {
                return new FunctionResult(this.Name, this.PluginName, context, result.Value);
            }
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            this._logger?.LogError(ex, "Semantic function {Plugin}.{Name} execution failed with error {Error}", this.PluginName, this.Name, ex.Message);
            throw;
        }

        return result;
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

        eventWrapper.EventArgs = new FunctionInvokingEventArgs(this.Describe(), context)
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

        eventWrapper.EventArgs = new FunctionInvokedEventArgs(this.Describe(), result);
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

    #endregion

    #region Obsolete

    /// <inheritdoc/>
    [Obsolete("Use ISKFunction.ModelSettings instead. This will be removed in a future release.")]
    public AIRequestSettings? RequestSettings => this._promptTemplateConfig.ModelSettings?.FirstOrDefault<AIRequestSettings>();

    /// <inheritdoc/>
    [Obsolete("Use ISKFunction.SetAIServiceFactory instead. This will be removed in a future release.")]
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        Verify.NotNull(serviceFactory);

        if (this._serviceSelector is DelegatingAIServiceSelector delegatingProvider)
        {
            delegatingProvider.ServiceFactory = serviceFactory;
        }
        else
        {
            var serviceSelector = new DelegatingAIServiceSelector();
            serviceSelector.ServiceFactory = serviceFactory;
            this._serviceSelector = serviceSelector;
        }
        return this;
    }

    /// <inheritdoc/>
    [Obsolete("Use ISKFunction.SetAIRequestSettingsFactory instead. This will be removed in a future release.")]
    public ISKFunction SetAIConfiguration(AIRequestSettings? requestSettings)
    {
        if (this._serviceSelector is DelegatingAIServiceSelector delegatingProvider)
        {
            delegatingProvider.RequestSettings = requestSettings;
        }
        else
        {
            var configurationProvider = new DelegatingAIServiceSelector();
            configurationProvider.RequestSettings = requestSettings;
            this._serviceSelector = configurationProvider;
        }
        return this;
    }

    /// <inheritdoc/>
    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.PluginName instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public string SkillName => this.PluginName;

    /// <inheritdoc/>
    [Obsolete("Kernel no longer differentiates between Semantic and Native functions. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public bool IsSemantic => true;

    /// <inheritdoc/>
    [Obsolete("This method is a nop and will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction SetDefaultSkillCollection(IReadOnlyFunctionCollection skills) => this;

    /// <inheritdoc/>
    [Obsolete("This method is a nop and will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction SetDefaultFunctionCollection(IReadOnlyFunctionCollection functions) => this;

    #endregion
}
