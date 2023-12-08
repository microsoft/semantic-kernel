// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Services;
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

        (var aiService, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.Cancel is true)
        {
            throw new OperationCanceledException($"A {nameof(Kernel)}.{nameof(Kernel.PromptRendered)} event handler requested cancellation before function invocation.");
        }

        if (aiService is IChatCompletionService chatCompletion)
        {
            var chatContent = await chatCompletion.GetChatMessageContentAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
            return new FunctionResult(this, chatContent, kernel.Culture, chatContent.Metadata);
        }

        if (aiService is ITextGenerationService textGeneration)
        {
            var textContent = await textGeneration.GetTextContentWithDefaultParserAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
            return new FunctionResult(this, textContent, kernel.Culture, textContent.Metadata);
        }

        // This should never happen as the AI service is selected by the service selector
        throw new NotSupportedException($"The AI service {aiService.GetType()} is not supported. Supported services are {typeof(IChatCompletionService)} and {typeof(ITextGenerationService)}");
    }

    protected override async IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(
        Kernel kernel,
        KernelArguments arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(arguments);

        (var aiService, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.Cancel ?? false)
        {
            yield break;
        }

        IAsyncEnumerable<StreamingContentBase>? asyncReference = null;
        if (aiService is IChatCompletionService chatCompletion)
        {
            asyncReference = chatCompletion.GetStreamingChatMessageContentsAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken);
        }
        else if (aiService is ITextGenerationService textGeneration)
        {
            asyncReference = textGeneration.GetStreamingTextContentsWithDefaultParserAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken);
        }
        else
        {
            // This should never happen as the AI service is selected by the service selector
            throw new NotSupportedException($"The AI service {aiService.GetType()} is not supported. Supported services are {typeof(IChatCompletionService)} and {typeof(ITextGenerationService)}");
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

    private async Task<(IAIService, string, PromptRenderedEventArgs?)> RenderPromptAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        var serviceSelector = kernel.ServiceSelector;
        IAIService? aiService;
        PromptExecutionSettings? defaultExecutionSettings;

        //TODO: Revisit if SelectAIService implementation should return null when no service is found

#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            (aiService, defaultExecutionSettings) = serviceSelector.SelectAIService<IChatCompletionService>(kernel, this, arguments);
        }
        catch
        {
            // Fallback to text generation service, if the selector don't finds it, will throw.
            (aiService, defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, this, arguments);
        }
#pragma warning restore CA1031 // Do not catch general exception types

        Verify.NotNull(aiService);

        arguments.ExecutionSettings ??= defaultExecutionSettings;

        kernel.OnPromptRendering(this, arguments);

        var renderedPrompt = await this._promptTemplate.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        var renderedEventArgs = kernel.OnPromptRendered(this, arguments, renderedPrompt);

        return (aiService, renderedPrompt, renderedEventArgs);
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";

    #endregion
}
