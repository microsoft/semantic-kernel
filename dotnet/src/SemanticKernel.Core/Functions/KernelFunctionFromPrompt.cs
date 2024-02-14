// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A Semantic Kernel "Semantic" prompt function.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class KernelFunctionFromPrompt : KernelFunction
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="promptTemplate">Prompt template for the function, defined using the <see cref="PromptTemplateConfig.SemanticKernelTemplateFormat"/> template format.</param>
    /// <param name="executionSettings">Default execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">Optional format of the template. Must be provided if a prompt template factory is provided</param>
    /// <param name="promptTemplateFactory">Optional: Prompt template factory</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    public static KernelFunction Create(
        string promptTemplate,
        Dictionary<string, PromptExecutionSettings>? executionSettings = null,
        string? functionName = null,
        string? description = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(promptTemplate);

        if (promptTemplateFactory is not null)
        {
            if (string.IsNullOrWhiteSpace(templateFormat))
            {
                throw new ArgumentException($"Template format is required when providing a {nameof(promptTemplateFactory)}", nameof(templateFormat));
            }
        }

        var promptConfig = new PromptTemplateConfig
        {
            TemplateFormat = templateFormat ?? PromptTemplateConfig.SemanticKernelTemplateFormat,
            Name = functionName,
            Description = description ?? "Generic function, unknown purpose",
            Template = promptTemplate
        };

        if (executionSettings is not null)
        {
            promptConfig.ExecutionSettings = executionSettings;
        }

        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(loggerFactory);

        return Create(
            promptTemplate: factory.Create(promptConfig),
            promptConfig: promptConfig,
            loggerFactory: loggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template configuration.
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
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template and a prompt template configuration.
    /// </summary>
    /// <param name="promptTemplate">Prompt template for the function, defined using the <see cref="PromptTemplateConfig.SemanticKernelTemplateFormat"/> template format.</param>
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

        var result = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

#pragma warning disable CS0612 // Events are deprecated
        if (result.RenderedEventArgs?.Cancel is true)
        {
            throw new OperationCanceledException($"A {nameof(Kernel)}.{nameof(Kernel.PromptRendered)} event handler requested cancellation after prompt rendering.");
        }
#pragma warning restore CS0612 // Events are deprecated

        if (result.RenderedContext?.Cancel is true)
        {
            throw new OperationCanceledException("A prompt filter requested cancellation after prompt rendering.");
        }

        if (result.AIService is IChatCompletionService chatCompletion)
        {
            var chatContent = await chatCompletion.GetChatMessageContentAsync(result.RenderedPrompt, result.ExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
            this.CaptureUsageDetails(chatContent.ModelId, chatContent.Metadata, this._logger);
            return new FunctionResult(this, chatContent, kernel.Culture, chatContent.Metadata);
        }

        if (result.AIService is ITextGenerationService textGeneration)
        {
            var textContent = await textGeneration.GetTextContentWithDefaultParserAsync(result.RenderedPrompt, result.ExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
            this.CaptureUsageDetails(textContent.ModelId, textContent.Metadata, this._logger);
            return new FunctionResult(this, textContent, kernel.Culture, textContent.Metadata);
        }

        // The service selector didn't find an appropriate service. This should only happen with a poorly implemented selector.
        throw new NotSupportedException($"The AI service {result.AIService.GetType()} is not supported. Supported services are {typeof(IChatCompletionService)} and {typeof(ITextGenerationService)}");
    }

    protected override async IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(
        Kernel kernel,
        KernelArguments arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(arguments);

        var result = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

#pragma warning disable CS0612 // Events are deprecated
        if (result.RenderedEventArgs?.Cancel is true)
        {
            yield break;
        }
#pragma warning restore CS0612 // Events are deprecated

        if (result.RenderedContext?.Cancel is true)
        {
            yield break;
        }

        IAsyncEnumerable<StreamingKernelContent>? asyncReference = null;

        if (result.AIService is IChatCompletionService chatCompletion)
        {
            asyncReference = chatCompletion.GetStreamingChatMessageContentsAsync(result.RenderedPrompt, result.ExecutionSettings, kernel, cancellationToken);
        }
        else if (result.AIService is ITextGenerationService textGeneration)
        {
            asyncReference = textGeneration.GetStreamingTextContentsWithDefaultParserAsync(result.RenderedPrompt, result.ExecutionSettings, kernel, cancellationToken);
        }
        else
        {
            // The service selector didn't find an appropriate service. This should only happen with a poorly implemented selector.
            throw new NotSupportedException($"The AI service {result.AIService.GetType()} is not supported. Supported services are {typeof(IChatCompletionService)} and {typeof(ITextGenerationService)}");
        }

        await foreach (var content in asyncReference)
        {
            cancellationToken.ThrowIfCancellationRequested();

            yield return typeof(TResult) switch
            {
                _ when typeof(TResult) == typeof(string)
                    => (TResult)(object)content.ToString(),

                _ when content is TResult contentAsT
                    => contentAsT,

                _ when content.InnerContent is TResult innerContentAsT
                    => innerContentAsT,

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
            promptConfig.Name ?? CreateRandomFunctionName(),
            promptConfig.Description ?? string.Empty,
            promptConfig.GetKernelParametersMetadata(),
            promptConfig.GetKernelReturnParameterMetadata(),
            promptConfig.ExecutionSettings)
    {
        this._logger = loggerFactory?.CreateLogger(typeof(KernelFunctionFactory)) ?? NullLogger.Instance;

        this._promptTemplate = template;
        this._inputVariables = promptConfig.InputVariables.Select(iv => new InputVariable(iv)).ToList();
    }

    #region private

    private readonly ILogger _logger;
    private readonly List<InputVariable> _inputVariables;
    private readonly IPromptTemplate _promptTemplate;

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrWhiteSpace(this.Description) ? this.Name : $"{this.Name} ({this.Description})";

    /// <summary>The measurement tag name for the model used.</summary>
    private const string MeasurementModelTagName = "semantic_kernel.function.model_id";

    /// <summary><see cref="Counter{T}"/> to record function invocation prompt token usage.</summary>
    private static readonly Histogram<int> s_invocationTokenUsagePrompt = s_meter.CreateHistogram<int>(
        name: "semantic_kernel.function.invocation.token_usage.prompt",
        unit: "{token}",
        description: "Measures the prompt token usage");

    /// <summary><see cref="Counter{T}"/> to record function invocation completion token usage.</summary>
    private static readonly Histogram<int> s_invocationTokenUsageCompletion = s_meter.CreateHistogram<int>(
        name: "semantic_kernel.function.invocation.token_usage.completion",
        unit: "{token}",
        description: "Measures the completion token usage");

    /// <summary>Add default values to the arguments if an argument is not defined</summary>
    private void AddDefaultValues(KernelArguments arguments)
    {
        foreach (var parameter in this._inputVariables)
        {
            if (!arguments.ContainsName(parameter.Name) && parameter.Default != null)
            {
                arguments[parameter.Name] = parameter.Default;
            }
        }
    }

    private async Task<PromptRenderingResult> RenderPromptAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        var serviceSelector = kernel.ServiceSelector;
        IAIService? aiService;

        // Try to use IChatCompletionService.
        if (serviceSelector.TrySelectAIService<IChatCompletionService>(
            kernel, this, arguments,
            out IChatCompletionService? chatService, out PromptExecutionSettings? executionSettings))
        {
            aiService = chatService;
        }
        else
        {
            // If IChatCompletionService isn't available, try to fallback to ITextGenerationService,
            // throwing if it's not available.
            (aiService, executionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, this, arguments);
        }

        Verify.NotNull(aiService);

#pragma warning disable CS0618 // Events are deprecated
        kernel.OnPromptRendering(this, arguments);
#pragma warning restore CS0618 // Events are deprecated

        kernel.OnPromptRenderingFilter(this, arguments);

        var renderedPrompt = await this._promptTemplate.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this._logger.LogTrace("Rendered prompt: {Prompt}", renderedPrompt);
        }

#pragma warning disable CS0618 // Events are deprecated
        var renderedEventArgs = kernel.OnPromptRendered(this, arguments, renderedPrompt);

        if (renderedEventArgs is not null &&
            !renderedEventArgs.Cancel &&
            renderedEventArgs.RenderedPrompt != renderedPrompt)
        {
            renderedPrompt = renderedEventArgs.RenderedPrompt;

            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this._logger.LogTrace("Rendered prompt changed by event handler: {Prompt}", renderedEventArgs.RenderedPrompt);
            }
        }
#pragma warning restore CS0618 // Events are deprecated

        var renderedContext = kernel.OnPromptRenderedFilter(this, arguments, renderedPrompt);

        if (renderedContext is not null &&
            !renderedContext.Cancel &&
            renderedContext.RenderedPrompt != renderedPrompt)
        {
            renderedPrompt = renderedContext.RenderedPrompt;

            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this._logger.LogTrace("Rendered prompt changed by prompt filter: {Prompt}", renderedContext.RenderedPrompt);
            }
        }

        return new(aiService, renderedPrompt)
        {
            ExecutionSettings = executionSettings,
            RenderedEventArgs = renderedEventArgs,
            RenderedContext = renderedContext
        };
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string CreateRandomFunctionName() => $"func{Guid.NewGuid():N}";

    /// <summary>
    /// Captures usage details, including token information.
    /// </summary>
    private void CaptureUsageDetails(string? modelId, IReadOnlyDictionary<string, object?>? metadata, ILogger logger)
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

        var jsonObject = default(JsonElement);
        try
        {
            jsonObject = JsonSerializer.SerializeToElement(usageObject);
        }
        catch (Exception ex) when (ex is NotSupportedException)
        {
            logger.LogWarning(ex, "Error while parsing usage details from model result.");
            return;
        }

        if (jsonObject.TryGetProperty("PromptTokens", out var promptTokensJson) &&
            promptTokensJson.TryGetInt32(out int promptTokens) &&
            jsonObject.TryGetProperty("CompletionTokens", out var completionTokensJson) &&
            completionTokensJson.TryGetInt32(out int completionTokens))
        {
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
        else
        {
            logger.LogWarning("Unable to get token details from model result.");
        }
    }

    #endregion
}
