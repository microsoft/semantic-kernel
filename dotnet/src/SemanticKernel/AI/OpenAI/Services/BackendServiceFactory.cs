// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Backend service factory.
/// </summary>
internal sealed class BackendServiceFactory : IBackendServiceFactory
{
    /// <summary>
    /// Initializes a new instance of the <see cref="BackendServiceFactory"/> class.
    /// </summary>
    /// <param name="httpClientFactory">The Http client factory.</param>
    /// <param name="logger">The logger.</param>
    public BackendServiceFactory(IHttpClientFactory httpClientFactory, ILogger? logger)
    {
        Verify.NotNull(httpClientFactory, "Http client pool is not set to an instance of an object.");

        this._httpClientFactory = httpClientFactory;
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <inheritdoc/>
    public IEmbeddingGenerator<string, float> CreateEmbeddingGenerator(IBackendConfig config)
    {
        switch (config)
        {
            case AzureOpenAIConfig azureOpenAIConfig:
            {
                var serviceClient = this.CreateAzureOpenAIServiceClient(azureOpenAIConfig);

                var deploymentProvider = new AzureOpenAIDeploymentProvider(serviceClient, azureOpenAIConfig.Endpoint);

                return new AzureTextEmbeddings(
                    serviceClient,
                    deploymentProvider,
                    azureOpenAIConfig.DeploymentName);
            }

            case OpenAIConfig openAIConfig:
            {
                var serviceClient = this.CreatesOpenAIServiceClient(openAIConfig);

                return new OpenAITextEmbeddings(
                    serviceClient,
                    openAIConfig.ModelId);
            }

            default:
            {
                throw new AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    $"Unknown/unsupported backend type {config.GetType():G}, unable to prepare semantic memory.");
            }
        }
    }

    /// <inheritdoc/>
    public ITextCompletionClient CreateTextCompletionClient(IBackendConfig config, string functionDescription)
    {
        switch (config)
        {
            case AzureOpenAIConfig azureOpenAIConfig:
            {
                var serviceClient = this.CreateAzureOpenAIServiceClient(azureOpenAIConfig);

                var deploymentProvider = new AzureOpenAIDeploymentProvider(serviceClient, azureOpenAIConfig.Endpoint);

                return new AzureTextCompletion(
                    serviceClient,
                    deploymentProvider,
                    azureOpenAIConfig.DeploymentName);
            }

            case OpenAIConfig openAIConfig:
            {
                var serviceClient = this.CreatesOpenAIServiceClient(openAIConfig);

                return new OpenAITextCompletion(
                    serviceClient,
                    openAIConfig.ModelId);
            }

            default:
            {
                throw new AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    $"Unknown/unsupported backend configuration type {config.GetType():G}, unable to prepare semantic function. " +
                    $"Function description: {functionDescription}");
            }
        }
    }

    /// <summary>
    /// Creates an instance of the AzureOpenAIServiceClient class.
    /// </summary>
    /// <param name="config">The service client configuration.</param>
    /// <returns>An instance of the AzureOpenAIServiceClient class.</returns>
    private IAzureOpenAIServiceClient CreateAzureOpenAIServiceClient(AzureOpenAIConfig config)
    {
        HttpMessageHandler CreateHandlers()
        {
            //Resiliency, logging, authentication handlers can be configured here.
            return new HttpClientHandler() { CheckCertificateRevocationList = true };
        }

        var httpClient = this.GetOrCreateHttpClient(config.Endpoint, CreateHandlers);

        return new AzureOpenAIServiceClient(httpClient, config.APIKey, config.APIVersion, this._logger);
    }

    /// <summary>
    /// Returns an instance of the OpenAIServiceClient class.
    /// </summary>
    /// <param name="config">The service client configuration.</param>
    /// <returns>An instance of the OpenAIServiceClient class.</returns>
    private IOpenAIServiceClient CreatesOpenAIServiceClient(OpenAIConfig config)
    {
        //TODO: make it configurable.
        var baseUri = "https://api.openai.com/v1";

        HttpMessageHandler CreateHandlers()
        {
            //Resiliency, logging, authentication handlers can be configured here.
            return new HttpClientHandler() { CheckCertificateRevocationList = true };
        }

        var httpClient = this.GetOrCreateHttpClient(baseUri, CreateHandlers);

        return new OpenAIServiceClient(httpClient, config.APIKey, config.OrgId, this._logger);
    }

    /// <summary>
    /// Returns a cached instance of the HttpClient class or creates a new one.
    /// </summary>
    /// <param name="baseUri">The base uri.</param>
    /// <param name="handlerProvider">HttpMessageHandler provider.</param>
    /// <returns></returns>
    private HttpClient GetOrCreateHttpClient(string baseUri, Func<HttpMessageHandler> handlerProvider)
    {
        return this._httpClientsCache.GetOrAdd(baseUri, (_) =>
        {
            var client = this._httpClientFactory.Create(handlerProvider.Invoke(), true);

            client.BaseAddress = new Uri(baseUri, UriKind.Absolute);

            client.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);

            return client;
        });
    }

    #region private ================================================================================

    /// <summary>
    /// The user agent.
    /// </summary>
    private const string HttpUserAgent = "Microsoft Semantic Kernel";

    /// <summary>
    /// The logger.
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The Http client factory.
    /// </summary>
    private readonly IHttpClientFactory _httpClientFactory;

    /// <summary>
    /// Http clients cache.
    /// </summary>
    private readonly ConcurrentDictionary<string, HttpClient> _httpClientsCache = new();

    #endregion
}
