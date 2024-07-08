// Copyright (c) Microsoft. All rights reserved.
using System.ClientModel.Primitives;
using System.Net.Http;
using System.Threading;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

internal static class OpenAIClientFactory
{
    /// <summary>
    /// Avoids an exception from OpenAI Client when a custom endpoint is provided without an API key.
    /// </summary>
    private const string SingleSpaceKey = " ";

    /// <summary>
    /// Creates an OpenAI client based on the provided configuration.
    /// </summary>
    /// <param name="config">Configuration required to target a specific Open AI service</param>
    /// <returns>An initialized Open AI client</returns>
    public static OpenAIClient CreateClient(OpenAIServiceConfiguration config)
    {
        // Inspect options
        switch (config.Type)
        {
            case OpenAIServiceConfiguration.OpenAIServiceType.AzureOpenAI:
            {
                AzureOpenAIClientOptions clientOptions = CreateAzureClientOptions(config);

                if (config.Credential is not null)
                {
                    return new AzureOpenAIClient(config.Endpoint, config.Credential, clientOptions);
                }
                if (!string.IsNullOrEmpty(config.ApiKey))
                {
                    return new AzureOpenAIClient(config.Endpoint, config.ApiKey!, clientOptions);
                }

                throw new KernelException($"Unsupported configuration type: {config.Type}");
            }
            case OpenAIServiceConfiguration.OpenAIServiceType.OpenAI:
            {
                OpenAIClientOptions clientOptions = CreateOpenAIClientOptions(config);
                return new OpenAIClient(config.ApiKey ?? SingleSpaceKey, clientOptions);
            }
            default:
                throw new KernelException($"Unsupported configuration state: {config.Type}");
        }
    }

    private static AzureOpenAIClientOptions CreateAzureClientOptions(OpenAIServiceConfiguration config)
    {
        AzureOpenAIClientOptions options =
            new()
            {
                ApplicationId = HttpHeaderConstant.Values.UserAgent,
                Endpoint = config.Endpoint,
            };

        ConfigureClientOptions(config.HttpClient, options);

        return options;
    }

    private static OpenAIClientOptions CreateOpenAIClientOptions(OpenAIServiceConfiguration config)
    {
        OpenAIClientOptions options =
            new()
            {
                ApplicationId = HttpHeaderConstant.Values.UserAgent,
                Endpoint = config.Endpoint ?? config.HttpClient?.BaseAddress,
            };

        ConfigureClientOptions(config.HttpClient, options);

        return options;
    }

    private static void ConfigureClientOptions(HttpClient? httpClient, OpenAIClientOptions options)
    {
        options.AddPolicy(CreateRequestHeaderPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIAssistantAgent))), PipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientPipelineTransport(httpClient);
            options.RetryPolicy = new ClientRetryPolicy(maxRetries: 0); // Disable retry policy if and only if a custom HttpClient is provided.
            options.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable default timeout
        }
    }

    private static GenericActionPipelinePolicy CreateRequestHeaderPolicy(string headerName, string headerValue)
        =>
            new((message) =>
                {
                    if (message?.Request?.Headers?.TryGetValue(headerName, out string? _) == false)
                    {
                        message.Request.Headers.Set(headerName, headerValue);
                    }
                });
}
