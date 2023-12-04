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
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Events;

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

        (var textCompletion, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.Cancel is true)
        {
            throw new OperationCanceledException($"A {nameof(Kernel)}.{nameof(Kernel.PromptRendered)} event handler requested cancellation before function invocation.");
        }

        var textContent = await textCompletion.GetTextContentAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);

        IDictionary<string, object?> metadata = textContent.Metadata ?? new Dictionary<string, object?>();
        metadata.Add(KernelEventArgsExtensions.RenderedPromptMetadataKey, renderedPrompt);

        return new FunctionResult(this, textContent.Text, kernel.Culture, new Dictionary<string, object?>(metadata));
    }

    protected override async IAsyncEnumerable<T> InvokeCoreStreamingAsync<T>(
        Kernel kernel,
        KernelArguments arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.AddDefaultValues(arguments);

        (var textCompletion, var renderedPrompt, var renderedEventArgs) = await this.RenderPromptAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        if (renderedEventArgs?.Cancel ?? false)
        {
            yield break;
        }

        await foreach (var content in textCompletion.GetStreamingTextContentsAsync(renderedPrompt, arguments.ExecutionSettings, kernel, cancellationToken))
        {
            cancellationToken.ThrowIfCancellationRequested();

            yield return typeof(T) switch
            {
                _ when typeof(T) == typeof(string)
                    => (T)(object)content.ToString(),

                _ when content is T contentAsT
                    => (T)contentAsT,

                _ when content.InnerContent is T innerContentAsT
                    => (T)innerContentAsT,

                _ when typeof(T) == typeof(byte[])
                    => (T)(object)content.ToByteArray(),

                _ => throw new NotSupportedException($"The specific type {typeof(T)} is not supported. Support types are {typeof(StreamingTextContent)}, string, byte[], or a matching type for {typeof(StreamingTextContent)}.{nameof(StreamingTextContent.InnerContent)} property")
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

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrWhiteSpace(this.Description) ? this.Name : $"{this.Name} ({this.Description})";

    /// <summary>Add default values to the arguments if an argument is not defined</summary>
    private void AddDefaultValues(KernelArguments arguments)
    {
        foreach (var parameter in this._promptConfig.InputParameters)
        {
            if (!arguments.ContainsName(parameter.Name) && parameter.DefaultValue != null)
            {
                arguments[parameter.Name] = parameter.DefaultValue;
            }
        }
    }

    private async Task<(ITextCompletion, string, PromptRenderedEventArgs?)> RenderPromptAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        var serviceSelector = kernel.GetService<IAIServiceSelector>();
        (var textCompletion, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, this, arguments);
        Verify.NotNull(textCompletion);

        arguments.ExecutionSettings ??= defaultExecutionSettings;

        kernel.OnPromptRendering(this, arguments);

        var renderedPrompt = await this._promptTemplate.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        var renderedEventArgs = kernel.OnPromptRendered(this, arguments, renderedPrompt);

        return (textCompletion, renderedPrompt, renderedEventArgs);
    }

    /// <summary>Create a random, valid function name.</summary>
    private static string RandomFunctionName() => $"func{Guid.NewGuid():N}";

    #endregion
}
