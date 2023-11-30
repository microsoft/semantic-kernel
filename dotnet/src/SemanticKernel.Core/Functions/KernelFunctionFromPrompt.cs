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
    /// <param name="executionSettings">Optional LLM request settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="promptTemplateFactory">Optional: Prompt template factory</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    public static KernelFunction Create(
        string promptTemplate,
        PromptExecutionSettings? executionSettings = null,
        string? functionName = null,
        string? description = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var promptConfig = new PromptTemplateConfig
        {
            Name = functionName ?? RandomFunctionName(),
            Description = description ?? "Generic function, unknown purpose",
            Template = promptTemplate
        };

        if (executionSettings is not null)
        {
            promptConfig.ExecutionSettings.Add(executionSettings);
        }

        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(loggerFactory);

        return Create(
            promptTemplate: factory.Create(promptConfig),
            promptConfig: promptConfig,
            loggerFactory: loggerFactory);
    }

    /// <summary>
    /// Creates a string-to-string semantic function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="promptConfig">Prompt template configuration</param>
    /// <param name="promptTemplateFactory">Optional: Prompt template factory</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    public static KernelFunction Create(
        PromptTemplateConfig promptConfig,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(loggerFactory);

        return Create(
            promptTemplate: factory.Create(promptConfig),
            promptConfig: promptConfig,
            loggerFactory: loggerFactory);
    }

    /// <summary>
    /// Allow to define a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="promptConfig">Prompt template configuration.</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    public static KernelFunction Create(
        IPromptTemplate promptTemplate,
        PromptTemplateConfig promptConfig,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(promptTemplate);
        Verify.NotNull(promptConfig);

        if (string.IsNullOrEmpty(promptConfig.Name))
        {
            promptConfig.Name = RandomFunctionName();
        }
        Verify.ValidFunctionName(promptConfig.Name);

        return new KernelFunctionFromPrompt(
            template: promptTemplate,
            promptConfig: promptConfig,
            loggerFactory: loggerFactory);
    }

    /// <inheritdoc/>
    protected override async Task<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(arguments);

        try
        {
            (var textCompletion, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
            if (renderedEventArgs?.CancelToken.IsCancellationRequested ?? false)
            {
                return new FunctionResult(this.Name)
                {
                    IsCancellationRequested = true
                };
            }

            IReadOnlyList<ITextResult> completionResults = await textCompletion.GetCompletionsAsync(renderedPrompt, arguments.ExecutionSettings, cancellationToken).ConfigureAwait(false);

            string completion = await GetCompletionsResultContentAsync(completionResults, cancellationToken).ConfigureAwait(false);

            var modelResults = completionResults.Select(c => c.ModelResult).ToArray();

            var result = new FunctionResult(this.Name, completion, kernel.Culture);
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
        KernelArguments arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(arguments);

        (var textCompletion, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.CancelToken.IsCancellationRequested ?? false)
        {
            yield break;
        }

        await foreach (T genericChunk in textCompletion.GetStreamingContentAsync<T>(renderedPrompt, arguments.ExecutionSettings, cancellationToken))
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
        PromptTemplateConfig promptConfig,
        ILoggerFactory? loggerFactory = null) : base(promptConfig.Name, promptConfig.Description, promptConfig.GetKernelParametersMetadata(), null, promptConfig.ExecutionSettings)
    {
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(KernelFunctionFactory)) : NullLogger.Instance;

        this._promptTemplate = template;
        this._promptConfig = promptConfig;
    }

    #region private

    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptConfig;
    private readonly IPromptTemplate _promptTemplate;

    private static async Task<string> GetCompletionsResultContentAsync(IReadOnlyList<ITextResult> completions, CancellationToken cancellationToken = default)
    {
        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        return await completions[0].GetCompletionAsync(cancellationToken).ConfigureAwait(false);
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrWhiteSpace(this.Description) ? this.Name : $"{this.Name} ({this.Description})";

    /// <summary>Add default values to the arguments if an argument is not defined</summary>
    private void AddDefaultValues(KernelArguments arguments)
    {
        foreach (var parameter in this._promptConfig.InputParameters)
        {
            if (!arguments.ContainsKey(parameter.Name) && parameter.DefaultValue != null)
            {
                arguments[parameter.Name] = parameter.DefaultValue;
            }
        }
    }

    private async Task<(ITextCompletion, string, PromptRenderedEventArgs?)> RenderPromptAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        var serviceSelector = kernel.GetService<IAIServiceSelector>();
        (var textCompletion, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, this, arguments);
        Verify.NotNull(textCompletion);

        arguments.ExecutionSettings ??= defaultRequestSettings;

        kernel.OnPromptRendering(this, arguments);

        var renderedPrompt = await this._promptTemplate.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        var renderedEventArgs = kernel.OnPromptRendered(this, arguments, renderedPrompt);

        return (textCompletion, renderedPrompt, renderedEventArgs);
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";

    #endregion
}
