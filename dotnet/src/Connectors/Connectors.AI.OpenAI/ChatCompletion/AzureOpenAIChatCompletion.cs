// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/// <summary>
/// Azure OpenAI chat completion client.
/// </summary>
public sealed class AzureOpenAIChatCompletion : IChatCompletion, ITextCompletion
{
    /// <summary>Core implementation shared by Azure OpenAI clients.</summary>
    private readonly AzureOpenAIClientCore _core;

    /// <summary>
    /// Create an instance of the <see cref="AzureOpenAIChatCompletion"/> connector with API key auth.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIChatCompletion(
        string deploymentName,
        string endpoint,
        string apiKey,
        string modelId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._core = new(deploymentName, endpoint, apiKey, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIChatCompletion)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Create an instance of the <see cref="AzureOpenAIChatCompletion"/> connector with AAD auth.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIChatCompletion(
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string modelId,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._core = new(deploymentName, endpoint, credentials, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIChatCompletion)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAIChatCompletion"/> client instance using the specified <see cref="OpenAIClient"/>.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIChatCompletion(
        string deploymentName,
        OpenAIClient openAIClient,
        string modelId,
        ILoggerFactory? loggerFactory = null)
    {
        this._core = new(deploymentName, openAIClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIChatCompletion)));

        this._core.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null) =>
        ClientCore.CreateNewChat(instructions);

    /// <inheritdoc/>
    public Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this._core.LogActionDetails();

        return this._core.GetChatResultsAsync(chat, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        this._core.LogActionDetails();

        return this._core.GetChatResultsAsTextAsync(prompt, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var chatHistory = this.CreateChatHistory(prompt, executionSettings);
        return this._core.GetChatResultsAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<T> GetStreamingContentAsync<T>(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var chatHistory = this.CreateChatHistory(prompt, executionSettings);

        return this._core.GetChatStreamingUpdatesAsync<T>(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <summary>Creates a new chat history from the specified prompt and execution settings.</summary>
    private OpenAIChatHistory CreateChatHistory(string prompt, PromptExecutionSettings? executionSettings)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        this._core.LogActionDetails();

        var openAIExecutionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        return ClientCore.CreateNewChat(prompt, openAIExecutionSettings);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<T> GetStreamingContentAsync<T>(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this._core.LogActionDetails();

        return this._core.GetChatStreamingUpdatesAsync<T>(chatHistory, executionSettings, kernel, cancellationToken);
    }
}
