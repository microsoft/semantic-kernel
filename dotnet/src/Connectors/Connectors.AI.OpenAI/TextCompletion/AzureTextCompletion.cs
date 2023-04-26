// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/// <summary>
/// Azure OpenAI text completion client.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class AzureTextCompletion : AzureOpenAIClientBase, ITextCompletion
{
    /// <summary>
    /// Creates a new AzureTextCompletion client instance using API Key auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP requests.</param>
    /// <param name="log">Application logger</param>
    public AzureTextCompletion(
        string modelId,
        string endpoint,
        string apiKey,
        IDelegatingHandlerFactory? handlerFactory = null,
        ILogger? log = null) : base(modelId, endpoint, apiKey, handlerFactory, log)
    {
    }

    /// <summary>
    /// Creates a new AzureTextCompletion client instance supporting AAD auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP requests.</param>
    /// <param name="log">Application logger</param>
    public AzureTextCompletion(
        string modelId,
        string endpoint,
        TokenCredential credentials,
        IDelegatingHandlerFactory? handlerFactory = null,
        ILogger? log = null) : base(modelId, endpoint, credentials, handlerFactory, log)
    {
    }

    /// <inheritdoc/>
    public Task<string> CompleteAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        return this.InternalCompleteTextAsync(text, requestSettings, cancellationToken);
    }
}
