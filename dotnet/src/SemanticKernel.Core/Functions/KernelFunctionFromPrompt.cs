// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;

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
    public IReadOnlyList<KernelParameterMetadata> Parameters => this._promptTemplate.Parameters;

    /// <inheritdoc/>
    protected override KernelFunctionMetadata GetMetadataCore() =>
        this._metadata ??=
        new KernelFunctionMetadata(this.Name)
        {
            Description = this._promptTemplateConfig.Description,
            Parameters = this.Parameters
        };

    /// <inheritdoc/>
    protected override async Task<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        ContextVariables variables,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(variables);

        try
        {
            (var textCompletion, var defaultRequestSettings, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, variables, requestSettings, cancellationToken).ConfigureAwait(false);
            if (renderedEventArgs?.CancelToken.IsCancellationRequested ?? false)
            {
                return new FunctionResult(this.Name, variables)
                {
                    IsCancellationRequested = true
                };
            }

            IReadOnlyList<ITextResult> completionResults = await textCompletion.GetCompletionsAsync(renderedPrompt, requestSettings ?? defaultRequestSettings, cancellationToken).ConfigureAwait(false);
            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            // Update the result with the completion
            variables.Update(completion);

            var modelResults = completionResults.Select(c => c.ModelResult).ToArray();

            var result = new FunctionResult(this.Name, variables, completion);

            result.Metadata.Add(AIFunctionResultExtensions.ModelResultsMetadataKey, modelResults);
            result.Metadata.Add(KernelEventArgsExtensions.RenderedPromptMetadataKey, renderedPrompt);

            return result;
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            this._logger?.LogError(ex, "Prompt function {Name} execution failed with error {Error}", this.Name, ex.Message);
            throw;
        }
    }

    protected override async IAsyncEnumerable<T> InvokeCoreStreamingAsync<T>(
        Kernel kernel,
        ContextVariables variables,
        AIRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(variables);

        (var textCompletion, var defaultRequestSettings, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, variables, requestSettings, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.CancelToken.IsCancellationRequested ?? false)
        {
            yield break;
        }

        await foreach (T genericChunk in textCompletion.GetStreamingContentAsync<T>(renderedPrompt, requestSettings ?? defaultRequestSettings, cancellationToken))
        {
            cancellationToken.ThrowIfCancellationRequested();
            yield return genericChunk;
        }

        // There is no post cancellation check to override the result as the stream data was already sent.
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
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(KernelFunctionFactory)) : NullLogger.Instance;

        this._promptTemplate = template;
        this._promptTemplateConfig = promptTemplateConfig;
        Verify.ParametersUniqueness(this.Parameters);
    }

    #region private

    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptTemplateConfig;
    private KernelFunctionMetadata? _metadata;
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

    private async Task<(ITextCompletion, AIRequestSettings?, string, PromptRenderedEventArgs?)> RenderPromptAsync(Kernel kernel, ContextVariables variables, AIRequestSettings? requestSettings, CancellationToken cancellationToken)
    {
        var serviceSelector = kernel.ServiceSelector;
        (var textCompletion, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, variables, this);
        Verify.NotNull(textCompletion);

        kernel.OnPromptRendering(this, variables, requestSettings ?? defaultRequestSettings);

        var renderedPrompt = await this._promptTemplate.RenderAsync(kernel, variables, cancellationToken).ConfigureAwait(false);

        var renderedEventArgs = kernel.OnPromptRendered(this, variables, renderedPrompt);

        return (textCompletion, defaultRequestSettings, renderedPrompt, renderedEventArgs);
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";

    #endregion
}
