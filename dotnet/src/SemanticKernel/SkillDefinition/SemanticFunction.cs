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
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;

namespace Microsoft.SemanticKernel.SkillDefinition;

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
    public string SkillName { get; }

    /// <inheritdoc/>
    public string Description { get; }

    /// <inheritdoc/>
    public bool IsSemantic => true;

    /// <inheritdoc/>
    public CompleteRequestSettings RequestSettings { get; private set; } = new();

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IList<ParameterView> Parameters { get; }

    /// <summary>
    /// Create a native function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="skillName">Name of the skill to which the function to create belongs.</param>
    /// <param name="functionName">Name of the function to create.</param>
    /// <param name="functionConfig">Semantic function configuration.</param>
    /// <param name="logger">Optional logger for the function.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>SK function instance.</returns>
    public static ISKFunction FromSemanticConfig(
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(functionConfig);

        var func = new SemanticFunction(
            template: functionConfig.PromptTemplate,
            description: functionConfig.PromptTemplateConfig.Description,
            skillName: skillName,
            functionName: functionName,
            logger: logger
        );

        return func;
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

    /// <inheritdoc/>
    public async Task<SKContext> InvokeAsync(
        SKContext context,
        CompleteRequestSettings? settings = null,
        CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(context.Variables);

        return await this.RunPromptAsync(this._aiService?.Value, settings ?? this.RequestSettings, context, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills)
    {
        this._skillCollection = skills;
        return this;
    }

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        Verify.NotNull(serviceFactory);
        this._aiService = new Lazy<ITextCompletion>(serviceFactory);
        return this;
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(CompleteRequestSettings settings)
    {
        Verify.NotNull(settings);
        this.RequestSettings = settings;
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
        string skillName,
        string functionName,
        string description,
        ILogger? logger = null)
    {
        Verify.NotNull(template);
        Verify.ValidSkillName(skillName);
        Verify.ValidFunctionName(functionName);

        this._logger = logger ?? NullLogger.Instance;

        this._promptTemplate = template;
        this.Parameters = template.GetParameters();
        Verify.ParametersUniqueness(this.Parameters);

        this.Name = functionName;
        this.SkillName = skillName;
        this.Description = description;
    }

    #region private

    private static readonly JsonSerializerOptions s_toStringStandardSerialization = new();
    private static readonly JsonSerializerOptions s_toStringIndentedSerialization = new() { WriteIndented = true };
    private readonly ILogger _logger;
    private IReadOnlySkillCollection? _skillCollection;
    private Lazy<ITextCompletion>? _aiService = null;
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

    private async Task<SKContext> RunPromptAsync(
        ITextCompletion? client,
        CompleteRequestSettings? requestSettings,
        SKContext context,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(client);
        Verify.NotNull(requestSettings);

        try
        {
            string renderedPrompt = await this._promptTemplate.RenderAsync(context, cancellationToken).ConfigureAwait(false);
            var completionResults = await client.GetCompletionsAsync(renderedPrompt, requestSettings, cancellationToken).ConfigureAwait(false);
            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            // Update the result with the completion
            context.Variables.Update(completion);

            context.ModelResults = completionResults.Select(c => c.ModelResult).ToArray();
        }
        catch (AIException ex)
        {
            const string Message = "Something went wrong while rendering the semantic function" +
                                   " or while executing the text completion. Function: {0}.{1}. Error: {2}. Details: {3}";
            this._logger?.LogError(ex, Message, this.SkillName, this.Name, ex.Message, ex.Detail);
            throw;
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            const string Message = "Something went wrong while rendering the semantic function" +
                                   " or while executing the text completion. Function: {0}.{1}. Error: {2}";
            this._logger?.LogError(ex, Message, this.SkillName, this.Name, ex.Message);
            throw;
        }

        return context;
    }

    #endregion
}
