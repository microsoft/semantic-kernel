// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.Azure;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal abstract class ClientCore
{
    private const int MaxResultsPerPrompt = 128;

    internal ClientCore(ILogger? logger = null)
    {
        this.Logger = logger ?? NullLogger.Instance;
    }

    /// <summary>
    /// Model Id or Deployment Name
    /// </summary>
    internal string DeploymentOrModelName { get; set; } = string.Empty;

    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    internal abstract OpenAIClient Client { get; }

    /// <summary>
    /// Logger instance
    /// </summary>
    internal ILogger Logger { get; set; }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = new();

    /// <summary>
    /// Instance of <see cref="Meter"/> for metrics.
    /// </summary>
    private static readonly Meter s_meter = new("Microsoft.SemanticKernel.Connectors.Azure");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of prompt tokens used.
    /// </summary>
    private static readonly Counter<int> s_promptTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.azure.tokens.prompt",
            unit: "{token}",
            description: "Number of prompt tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of completion tokens used.
    /// </summary>
    private static readonly Counter<int> s_completionTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.azure.tokens.completion",
            unit: "{token}",
            description: "Number of completion tokens used");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of tokens used.
    /// </summary>
    private static readonly Counter<int> s_totalTokensCounter =
        s_meter.CreateCounter<int>(
            name: "semantic_kernel.connectors.azure.tokens.total",
            unit: "{token}",
            description: "Number of tokens used");

    private static Dictionary<string, object?> GetChatChoiceMetadata(ChatCompletions completions, ChatChoice chatChoice)
    {
        return new Dictionary<string, object?>(12)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.Created), completions.Created },
            { nameof(completions.PromptFilterResults), completions.PromptFilterResults },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },
            { nameof(completions.Usage), completions.Usage },
            { nameof(chatChoice.ContentFilterResults), chatChoice.ContentFilterResults },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(chatChoice.FinishReason), chatChoice.FinishReason?.ToString() },

            { nameof(chatChoice.FinishDetails), chatChoice.FinishDetails },
            { nameof(chatChoice.LogProbabilityInfo), chatChoice.LogProbabilityInfo },
            { nameof(chatChoice.Index), chatChoice.Index },
            { nameof(chatChoice.Enhancements), chatChoice.Enhancements },
        };
    }

    private static Dictionary<string, object?> GetResponseMetadata(StreamingChatCompletionsUpdate completions)
    {
        return new Dictionary<string, object?>(4)
        {
            { nameof(completions.Id), completions.Id },
            { nameof(completions.Created), completions.Created },
            { nameof(completions.SystemFingerprint), completions.SystemFingerprint },

            // Serialization of this struct behaves as an empty object {}, need to cast to string to avoid it.
            { nameof(completions.FinishReason), completions.FinishReason?.ToString() },
        };
    }

    /// <summary>
    /// Generate a new chat message
    /// </summary>
    /// <param name="chat">Chat history</param>
    /// <param name="executionSettings">Execution settings for the completion API.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">Async cancellation token</param>
    /// <returns>Generated chat message in string format</returns>
    internal async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chat,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        // Convert the incoming execution settings to OpenAI settings.
        AzurePromptExecutionSettings chatExecutionSettings = AzurePromptExecutionSettings.FromExecutionSettings(executionSettings);
        ValidateMaxTokens(chatExecutionSettings.MaxTokens);

        // Create the Azure SDK ChatCompletionOptions instance from all available information.
        var chatOptions = CreateChatCompletionsOptions(chatExecutionSettings, chat, kernel, this.DeploymentOrModelName);

        // Make the request.
        var responseData = (await RunRequestAsync(() => this.Client.GetChatCompletionsAsync(chatOptions, cancellationToken)).ConfigureAwait(false)).Value;
        this.CaptureUsageDetails(responseData.Usage);
        if (responseData.Choices.Count == 0)
        {
            throw new KernelException("Chat completions not found");
        }

        return responseData.Choices.Select(chatChoice => new AzureChatMessageContent(chatChoice.Message, this.DeploymentOrModelName, GetChatChoiceMetadata(responseData, chatChoice))).ToList();
    }

    internal async IAsyncEnumerable<AzureStreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chat,
        PromptExecutionSettings? executionSettings,
        Kernel? kernel,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(chat);

        AzurePromptExecutionSettings chatExecutionSettings = AzurePromptExecutionSettings.FromExecutionSettings(executionSettings);

        ValidateMaxTokens(chatExecutionSettings.MaxTokens);

        var chatOptions = CreateChatCompletionsOptions(chatExecutionSettings, chat, kernel, this.DeploymentOrModelName);

        StringBuilder? contentBuilder = null;
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;

        // Make the request.
        var response = await RunRequestAsync(() => this.Client.GetChatCompletionsStreamingAsync(chatOptions, cancellationToken)).ConfigureAwait(false);

        // Reset state
        contentBuilder?.Clear();
        toolCallIdsByIndex?.Clear();
        functionNamesByIndex?.Clear();
        functionArgumentBuildersByIndex?.Clear();

        // Stream the response.
        IReadOnlyDictionary<string, object?>? metadata = null;
        string? streamedName = null;
        ChatRole? streamedRole = default;
        CompletionsFinishReason finishReason = default;
        await foreach (StreamingChatCompletionsUpdate update in response.ConfigureAwait(false))
        {
            metadata = GetResponseMetadata(update);
            streamedRole ??= update.Role;
            streamedName ??= update.AuthorName;
            finishReason = update.FinishReason ?? default;

            yield return new AzureStreamingChatMessageContent(update, update.ChoiceIndex ?? 0, this.DeploymentOrModelName, metadata) { AuthorName = streamedName };
        }
    }

    internal void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this.Attributes.Add(key, value);
        }
    }

    /// <summary>Gets options to use for an OpenAIClient</summary>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceVersion">Optional API version.</param>
    /// <returns>An instance of <see cref="OpenAIClientOptions"/>.</returns>
    internal static OpenAIClientOptions GetOpenAIClientOptions(HttpClient? httpClient, OpenAIClientOptions.ServiceVersion? serviceVersion = null)
    {
        OpenAIClientOptions options = serviceVersion is not null ?
            new(serviceVersion.Value) :
            new();

        options.Diagnostics.ApplicationId = HttpHeaderConstant.Values.UserAgent;
        options.AddPolicy(new AddHeaderRequestPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientCore))), HttpPipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientTransport(httpClient);
            options.RetryPolicy = new RetryPolicy(maxRetries: 0); // Disable Azure SDK retry policy if and only if a custom HttpClient is provided.
            options.Retry.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable Azure SDK default timeout
        }

        return options;
    }

    private static ChatCompletionsOptions CreateChatCompletionsOptions(
        AzurePromptExecutionSettings executionSettings,
        ChatHistory chatHistory,
        Kernel? kernel,
        string deploymentOrModelName)
    {
        if (executionSettings.ResultsPerPrompt is < 1 or > MaxResultsPerPrompt)
        {
            throw new ArgumentOutOfRangeException($"{nameof(executionSettings)}.{nameof(executionSettings.ResultsPerPrompt)}", executionSettings.ResultsPerPrompt, $"The value must be in range between 1 and {MaxResultsPerPrompt}, inclusive.");
        }

        var options = new ChatCompletionsOptions
        {
            MaxTokens = executionSettings.MaxTokens,
            Temperature = (float?)executionSettings.Temperature,
            NucleusSamplingFactor = (float?)executionSettings.TopP,
            FrequencyPenalty = (float?)executionSettings.FrequencyPenalty,
            PresencePenalty = (float?)executionSettings.PresencePenalty,
            ChoiceCount = executionSettings.ResultsPerPrompt,
            DeploymentName = deploymentOrModelName,
            Seed = executionSettings.Seed,
        };

        if (executionSettings.TokenSelectionBiases is not null)
        {
            foreach (var keyValue in executionSettings.TokenSelectionBiases)
            {
                options.TokenSelectionBiases.Add(keyValue.Key, keyValue.Value);
            }
        }

        if (executionSettings.StopSequences is { Count: > 0 })
        {
            foreach (var s in executionSettings.StopSequences)
            {
                options.StopSequences.Add(s);
            }
        }

        if (!string.IsNullOrWhiteSpace(executionSettings?.ChatSystemPrompt) && !chatHistory.Any(m => m.Role == AuthorRole.System))
        {
            options.Messages.Add(GetRequestMessage(new ChatMessageContent(AuthorRole.System, executionSettings!.ChatSystemPrompt)));
        }

        foreach (var message in chatHistory)
        {
            options.Messages.Add(GetRequestMessage(message));
        }

        return options;
    }

    private static ChatRequestMessage GetRequestMessage(ChatMessageContent message)
    {
        if (message.Role == AuthorRole.System)
        {
            return new ChatRequestSystemMessage(message.Content) { Name = message.AuthorName };
        }

        if (message.Role == AuthorRole.User || message.Role == AuthorRole.Tool)
        {
            if (message.Items is { Count: 1 } && message.Items.FirstOrDefault() is TextContent textContent)
            {
                return new ChatRequestUserMessage(textContent.Text) { Name = message.AuthorName };
            }

            return new ChatRequestUserMessage(message.Items.Select(static (KernelContent item) => (ChatMessageContentItem)(item switch
            {
                TextContent textContent => new ChatMessageTextContentItem(textContent.Text),
                ImageContent imageContent => new ChatMessageImageContentItem(imageContent.Uri),
                _ => throw new NotSupportedException($"Unsupported chat message content type '{item.GetType()}'.")
            })))
            { Name = message.AuthorName };
        }

        if (message.Role == AuthorRole.Assistant)
        {
            return new ChatRequestAssistantMessage(message.Content) { Name = message.AuthorName };
        }

        throw new NotSupportedException($"Role {message.Role} is not supported.");
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens.HasValue && maxTokens < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    private static async Task<T> RunRequestAsync<T>(Func<Task<T>> request)
    {
        try
        {
            return await request.Invoke().ConfigureAwait(false);
        }
        catch (RequestFailedException e)
        {
            throw e.ToHttpOperationException();
        }
    }

    /// <summary>
    /// Captures usage details, including token information.
    /// </summary>
    /// <param name="usage">Instance of <see cref="CompletionsUsage"/> with usage details.</param>
    private void CaptureUsageDetails(CompletionsUsage usage)
    {
        if (usage is null)
        {
            if (this.Logger.IsEnabled(LogLevel.Debug))
            {
                this.Logger.LogDebug("Usage information is not available.");
            }

            return;
        }

        if (this.Logger.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation(
                "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}. Total tokens: {TotalTokens}.",
                usage.PromptTokens, usage.CompletionTokens, usage.TotalTokens);
        }

        s_promptTokensCounter.Add(usage.PromptTokens);
        s_completionTokensCounter.Add(usage.CompletionTokens);
        s_totalTokensCounter.Add(usage.TotalTokens);
    }
}
