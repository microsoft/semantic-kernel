// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A Semantic Kernel "Semantic" prompt function.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class KernelFunctionFromPrompt : KernelFunction
{
    // TODO: Revise these Create method XML comments

    /// <summary>
    /// Creates a string-to-string prompt function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="promptTemplate">Plain language definition of the prompt function, using SK template language</param>
    /// <param name="executionSettings">Optional LLM execution settings</param>
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
        Verify.NotNullOrWhiteSpace(promptTemplate);

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
    /// Creates a string-to-string prompt function, with no direct support for input context.
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
    /// Allow to define a prompt function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="promptTemplate">Plain language definition of the prompt function, using SK template language</param>
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

    /// <inheritdoc/>j
    protected override async ValueTask<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(arguments);

        (var textGeneration, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.Cancel is true)
        {
            throw new OperationCanceledException($"A {nameof(Kernel)}.{nameof(Kernel.PromptRendered)} event handler requested cancellation before function invocation.");
        }

        var textContent = await textGeneration.GetTextContentWithDefaultParserAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);

        this.CaptureUsageDetails(textContent.ModelId, textContent.Metadata, this._logger);
        return new FunctionResult(this, textContent.Text, kernel.Culture, textContent.Metadata);
    }

    protected override async IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(
        Kernel kernel,
        KernelArguments arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(arguments);

        (var textGeneration, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.Cancel ?? false)
        {
            yield break;
        }

        await foreach (var content in textGeneration.GetStreamingTextContentsWithDefaultParserAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken))
        {
            cancellationToken.ThrowIfCancellationRequested();

            yield return typeof(TResult) switch
            {
                _ when typeof(TResult) == typeof(string)
                    => (TResult)(object)content.ToString(),

                _ when content is TResult contentAsT
                    => (TResult)contentAsT,

                _ when content.InnerContent is TResult innerContentAsT
                    => (TResult)innerContentAsT,

                _ when typeof(TResult) == typeof(byte[])
                    => (TResult)(object)content.ToByteArray(),

                _ => throw new NotSupportedException($"The specific type {typeof(TResult)} is not supported. Support types are {typeof(StreamingTextContent)}, string, byte[], or a matching type for {typeof(StreamingTextContent)}.{nameof(StreamingTextContent.InnerContent)} property")
            };
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
        ILoggerFactory? loggerFactory = null) : base(
            promptConfig.Name,
            promptConfig.Description,
            promptConfig.GetKernelParametersMetadata(),
            promptConfig.GetKernelReturnParameterMetadata(),
            promptConfig.ExecutionSettings)
    {
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(KernelFunctionFactory)) : NullLogger.Instance;

        this._promptTemplate = template;
        this._promptConfig = promptConfig;
    }

    #region private

    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptConfig;
    private readonly IPromptTemplate _promptTemplate;

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrWhiteSpace(this.Description) ? this.Name : $"{this.Name} ({this.Description})";

    /// <summary>The measurement tag name for the model used.</summary>
    private const string MeasurementModelTagName = "sk.function.model_id";

    /// <summary><see cref="Counter{T}"/> to record function invocation prompt token usage.</summary>
    private static readonly Histogram<int> s_invocationTokenUsagePrompt = meter.CreateHistogram<int>(
        name: "sk.function.invocation.token_usage.prompt",
        unit: "{token}",
        description: "Measures the prompt token usage");

    /// <summary><see cref="Counter{T}"/> to record function invocation completion token usage.</summary>
    private static readonly Histogram<int> s_invocationTokenUsageCompletion = meter.CreateHistogram<int>(
        name: "sk.function.invocation.token_usage.completion",
        unit: "{token}",
        description: "Measures the completion token usage");

    /// <summary>Add default values to the arguments if an argument is not defined</summary>
    private void AddDefaultValues(KernelArguments arguments)
    {
        foreach (var parameter in this._promptConfig.InputVariables)
        {
            if (!arguments.ContainsName(parameter.Name) && parameter.Default != null)
            {
                arguments[parameter.Name] = parameter.Default;
            }
        }
    }

    private async Task<(ITextGenerationService, string, PromptRenderedEventArgs?)> RenderPromptAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        var serviceSelector = kernel.ServiceSelector;
        (var textGeneration, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, this, arguments);
        Verify.NotNull(textGeneration);

        arguments.ExecutionSettings ??= defaultExecutionSettings;

        kernel.OnPromptRendering(this, arguments);

        var renderedPrompt = await this._promptTemplate.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        var renderedEventArgs = kernel.OnPromptRendered(this, arguments, renderedPrompt);

        return (textGeneration, renderedPrompt, renderedEventArgs);
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";

    /// <summary>
    /// Captures usage details, including token information.
    /// </summary>
    private void CaptureUsageDetails(string? modelId, IDictionary<string, object?>? metadata, ILogger logger)
    {
        if (!logger.IsEnabled(LogLevel.Information) &&
            !s_invocationTokenUsageCompletion.Enabled &&
            !s_invocationTokenUsagePrompt.Enabled)
        {
            // Bail early to avoid unnecessary work.
            return;
        }

        if (string.IsNullOrWhiteSpace(modelId))
        {
            logger.LogInformation("No model ID provided to capture usage details.");
            return;
        }

        if (metadata is null)
        {
            logger.LogInformation("No metadata provided to capture usage details.");
            return;
        }

        if (!metadata.TryGetValue("Usage", out object? usageObject) || usageObject is null)
        {
            logger.LogInformation("No usage details provided to capture usage details.");
            return;
        }

        var promptTokens = 0;
        var completionTokens = 0;
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            var jsonObject = JsonSerializer.SerializeToElement(usageObject);
            promptTokens = jsonObject.GetProperty("PromptTokens").GetInt32();
            completionTokens = jsonObject.GetProperty("CompletionTokens").GetInt32();
        }
        catch (Exception ex)
        {
            logger.LogWarning(ex, "Error while parsing usage details from model result.");
            return;
        }
#pragma warning restore CA1031 // Do not catch general exception types

        logger.LogInformation(
            "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}.",
            promptTokens, completionTokens);

        TagList tags = new() {
            { MeasurementFunctionTagName, this.Name },
            { MeasurementModelTagName, modelId }
        };

        s_invocationTokenUsagePrompt.Record(promptTokens, in tags);
        s_invocationTokenUsageCompletion.Record(completionTokens, in tags);
    }

    #endregion
}
