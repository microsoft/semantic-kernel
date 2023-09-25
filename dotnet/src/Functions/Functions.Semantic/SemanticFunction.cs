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
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;

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

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.PluginName instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public string SkillName => this.PluginName;
#pragma warning restore CS1591

    /// <inheritdoc/>
    public string Description { get; }

    /// <inheritdoc/>
    public AIRequestSettings? RequestSettings { get; private set; }

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters => this._promptTemplate.Parameters;

    /// <summary>
    /// Create a semantic function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="pluginName">Name of the plugin to which the function being created belongs.</param>
    /// <param name="functionName">Name of the function to create.</param>
    /// <param name="functionConfig">Semantic function configuration.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>SK function instance.</returns>
    public static ISKFunction FromSemanticConfig(
        string pluginName,
        string functionName,
        SemanticFunctionConfig functionConfig,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(functionConfig);

        var func = new SemanticFunction(
            template: functionConfig.PromptTemplate,
            description: functionConfig.PromptTemplateConfig.Description,
            pluginName: pluginName,
            functionName: functionName,
            loggerFactory: loggerFactory
        );
        func.SetAIConfiguration(functionConfig.PromptTemplateConfig.Completion);

        return func;
    }

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

        return await this.RunPromptAsync(this._aiService?.Value, requestSettings ?? this.RequestSettings, context, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public ISKFunction SetDefaultFunctionCollection(IReadOnlyFunctionCollection functions)
    {
        this._functionCollection = functions;
        return this;
    }

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.SetDefaultFunctionCollection instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public ISKFunction SetDefaultSkillCollection(IReadOnlyFunctionCollection skills) =>
        this.SetDefaultFunctionCollection(skills);

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        Verify.NotNull(serviceFactory);
        this._aiService = new Lazy<ITextCompletion>(serviceFactory);
        return this;
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(AIRequestSettings? requestSettings)
    {
        this.RequestSettings = requestSettings;
        return this;
    }

    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
        if (this._aiService is { IsValueCreated: true } aiService)
        {
            (aiService.Value as IDisposable)?.Dispose();
        }
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
        string pluginName,
        string functionName,
        string description,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(template);
        Verify.ValidPluginName(pluginName);
        Verify.ValidFunctionName(functionName);

        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(SemanticFunction)) : NullLogger.Instance;

        this._promptTemplate = template;
        Verify.ParametersUniqueness(this.Parameters);

        this.Name = functionName;
        this.PluginName = pluginName;
        this.Description = description;

        this._view = new(() => new(functionName, pluginName, description, this.Parameters));
    }

    #region private

    private static readonly JsonSerializerOptions s_toStringStandardSerialization = new();
    private static readonly JsonSerializerOptions s_toStringIndentedSerialization = new() { WriteIndented = true };
    private readonly ILogger _logger;
    private IReadOnlyFunctionCollection? _functionCollection;
    private Lazy<ITextCompletion>? _aiService = null;
    private Lazy<FunctionView> _view;
    public IPromptTemplate _promptTemplate { get; }

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
        ITextCompletion? client,
        AIRequestSettings? requestSettings,
        SKContext context,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(client);

        FunctionResult result;

        try
        {
            string renderedPrompt = await this._promptTemplate.RenderAsync(context, cancellationToken).ConfigureAwait(false);
            IReadOnlyList<ITextResult> completionResults = await client.GetCompletionsAsync(renderedPrompt, requestSettings, cancellationToken).ConfigureAwait(false);
            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            // Update the result with the completion
            context.Variables.Update(completion);

            var modelResults = completionResults.Select(c => c.ModelResult).ToArray();

            result = new FunctionResult(this.Name, this.PluginName, context, completion, modelResults);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            this._logger?.LogError(ex, "Semantic function {Plugin}.{Name} execution failed with error {Error}", this.PluginName, this.Name, ex.Message);
            throw;
        }

        return result;
    }

    #endregion

    #region Obsolete

    /// <inheritdoc/>
    [Obsolete("Kernel no longer differentiates between Semantic and Native functions. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public bool IsSemantic => true;

    #endregion
}
